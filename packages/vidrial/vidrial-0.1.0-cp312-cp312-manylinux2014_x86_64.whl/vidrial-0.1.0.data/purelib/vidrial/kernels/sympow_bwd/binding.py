from dataclasses import dataclass
from math import prod
import torch as th
from vidrial.jit.mosaic_types.types import Shape, Layout, Int
from vidrial.jit.mosaic_types.util import torch_dtype_to_c
from vidrial.jit.mosaic_types.util import layout_from_shape_stride
from vidrial.jit.jit import jit, render
from vidrial.jit.timingcache import ConfigTimingCache
from vidrial.jit.decorator import pickbest
from vidrial.kernels.sympow.dimensions import op_output_shape, sympow_dim, problem_dimensions
from vidrial.kernels.sympow.binding import configurations as fwd_configurations


# ------------------- Source Code -------------------

@dataclass
class SourceCode:
    T: str
    XSlabShape: Shape # [d,[b1,...]]
    p: int
    d_tile: int
    duplicate_correction: bool
    GXSlab: Layout
    GZSlab: Layout
    b_tile: int
    ZFrgShape: Shape
    SZTileLayout: Layout
    @property
    def template(self):
        return """
#include <cuda.h>
#include <cuda_runtime.h>
#include <iostream>
#include "cute/tensor.hpp"
#include "cutlass/cutlass.h"
#include "sympow_mosaic.cuh"
#include "sympow_bwd/kernel.cuh"

using namespace cute;
using namespace mosaic;

extern "C" void launch(void* __raw_X, void* __raw_Zgrad, void* __raw_Xgrad) {
    using T = {T};
    auto X = reinterpret_cast<T*>(__raw_X);
    auto Zgrad = reinterpret_cast<T*>(__raw_Zgrad);
    auto Xgrad = reinterpret_cast<T*>(__raw_Xgrad);
    using GXSlab = {GXSlab};
    using GZSlab = {GZSlab};
    constexpr int p = {p};
    constexpr int d_tile = {d_tile};
    constexpr int b_tile = {b_tile};
    using ZFrgShape = {ZFrgShape};
    constexpr bool duplicate_correction = {duplicate_correction};
    using XSlabShape = {XSlabShape};
    using ZSlabShape = decltype(sympow_shape<p, d_tile>(XSlabShape{}));
    using XTileShape = Shape<Int<d_tile>, Int<b_tile>>; 
    using ZTileShape = decltype(tpow_shape<p>(XTileShape{}));
    using SZTileLayout = {SZTileLayout};
    using ZFrgThr = decltype(zipped_divide(Layout<ZTileShape>{}, ZFrgShape{}));
    auto mos = SympowMosaic<T, p, XSlabShape, XTileShape, ZFrgThr, GZSlab, GXSlab, SZTileLayout>{};
    launch_tiled_sympow_bwd_kernel<duplicate_correction>(mos, X, Zgrad, Xgrad);
}
"""
    def __str__(self):
        return render(self.template, self.__dict__)

# ------------------- Binding -------------------
@dataclass
class BindingCfg:
    d: int
    bs: tuple[int, ...]
    X_shape: tuple[int, ...]
    Z_shape: tuple[int, ...]
    X_stride: tuple[int, ...]
    Z_stride: tuple[int, ...]
    power: int
    d_tile: int
    duplicate_correction: bool
    # Performance parameters (don't affect the output)
    b_tile: int
    ZFrgShape: Shape
    SZTileLayout: Layout
    dtype: th.dtype
    @classmethod
    def from_args(cls, X, Zgrad, Xgrad, power, d_tile, duplicate_correction, b_tile, ZFrgShape, SZTileLayout):
        assert X.dtype == Zgrad.dtype == Xgrad.dtype
        dtype = X.dtype
        assert X.shape == Xgrad.shape, "X and Xgrad must have the same shape"
        assert X.stride() == Xgrad.stride(), "X and Xgrad must have the same stride"
        bs, d, D = problem_dimensions(Zgrad.shape, X.shape, power, d_tile)
        assert Zgrad.shape == op_output_shape(X.shape, power, d_tile)
        return BindingCfg(d, bs, X.shape, Zgrad.shape, X.stride(), Zgrad.stride(),
                          power, d_tile, duplicate_correction, b_tile, ZFrgShape, SZTileLayout, dtype)
    @property
    def source(self):
        """ Conversion between the different variable name and shape conventions
                D = sympow_dim(d, power, d_tile)
                    Python                     c++
                X_shape=[P,D]      ->      GXSlabShape=[D,P]
                Z_shape=[P,tile_num, d_tile, ...]  ->  GZSlabShape=[[d_tile,...],tile_num],P]
        """
        p = self.power
        XSlabShape = Shape(Int(self.d), Shape(*[Int(b) for b in self.bs]))
        batch_num = len(self.bs)
        batch_dims = tuple(range(batch_num))
        X_py2cuda = (batch_num, batch_dims)
        Z_py2cuda = ((tuple(range(p+batch_num, batch_num, -1)), batch_num), batch_dims)
        GXSlab = layout_from_shape_stride(self.X_shape, self.X_stride, X_py2cuda)
        GZSlab = layout_from_shape_stride(self.Z_shape, self.Z_stride, Z_py2cuda)
        return SourceCode(
            T=torch_dtype_to_c(self.dtype),
            XSlabShape=XSlabShape,
            p=self.power,
            d_tile=self.d_tile,
            duplicate_correction=self.duplicate_correction,
            GXSlab=GXSlab,
            GZSlab=GZSlab,
            b_tile=self.b_tile,
            ZFrgShape=self.ZFrgShape,
            SZTileLayout=self.SZTileLayout,
        )

def binding(X, Zgrad, Xgrad, power, d_tile, duplicate_correction, b_tile, ZFrgShape, SZTileLayout):
    binding_cfg = BindingCfg.from_args(X, Zgrad, Xgrad, power, d_tile, duplicate_correction, b_tile, ZFrgShape, SZTileLayout)
    jit(name = "sympow_bwd",
        code = str(binding_cfg.source),
    )(X, Zgrad, Xgrad)


# ---------------------- Autotune --------------------------------
def configurations(args: dict) -> list[dict]:
    X, Zgrad, power, d_tile = args['X'], args['Zgrad'], args['power'], args['d_tile']
    return fwd_configurations(dict(Z=Zgrad, X=X, power=power, d_tile=d_tile))

def hash_fn(args: dict) -> str:
    Zgrad, X, power, d_tile = args['Zgrad'], args['X'], args['power'], args['d_tile']
    bs,d,D = problem_dimensions(Zgrad.shape, X.shape, power, d_tile)
    return f"Zgrad.shape={Zgrad.shape}-X.shape={X.shape}-power={power}-d_tile={d_tile}-D={D}-d={d}"

cache = ConfigTimingCache('sympow_bwd', hash_fn)
binding_autotuned = pickbest(cache=cache, sweep=configurations, verbose=True, allow_failure=True)(binding)


