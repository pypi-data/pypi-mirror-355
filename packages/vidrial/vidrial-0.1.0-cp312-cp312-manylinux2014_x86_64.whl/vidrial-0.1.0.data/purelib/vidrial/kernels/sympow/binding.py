from dataclasses import dataclass
from functools import lru_cache
from math import prod
import torch as th
from vidrial.jit.mosaic_types.types import Shape, Layout, Int
from vidrial.jit.mosaic_types.util import torch_dtype_to_c
from vidrial.jit.mosaic_types.util import layout_from_shape_stride
from vidrial.jit.jit import jit, render
from vidrial.jit.timingcache import ConfigTimingCache
from vidrial.jit.decorator import pickbest

from vidrial.kernels.sympow.dimensions import problem_dimensions, op_output_shape
from vidrial.kernels.mma_configurator import SMEM_LIMIT, dtype_to_bytes


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
#include <cute/tensor.hpp>
#include <cutlass/cutlass.h>
#include "sympow/kernel.cuh"
#include "sympow_mosaic.cuh"
using namespace cute;
using namespace mosaic;

extern "C" void launch(void* __raw_Z, void* __raw_X) {
    using T = {T};
    auto Z = reinterpret_cast<T*>(__raw_Z);
    auto X = reinterpret_cast<T*>(__raw_X);
    using XSlabShape = {XSlabShape};
    using GXSlab = decltype(static_tree_cast<int64_t>({GXSlab}{}));
    using GZSlab = decltype(static_tree_cast<int64_t>({GZSlab}{}));
    constexpr int p = {p};
    constexpr int d_tile = {d_tile};
    constexpr int b_tile = {b_tile};
    using ZFrgShape = {ZFrgShape};
    constexpr bool duplicate_correction = {duplicate_correction};
    using ZSlabShape = decltype(sympow_shape<p, d_tile>(XSlabShape{}));
    using XTileShape = Shape<Int<d_tile>, Int<b_tile>>; 
    using ZTileShape = decltype(tpow_shape<p>(XTileShape{}));
    using SZTileLayout = {SZTileLayout};
    using ZFrgThr = decltype(zipped_divide(Layout<ZTileShape>{}, ZFrgShape{}));
    auto mos = SympowMosaic<T, p, XSlabShape, XTileShape, ZFrgThr, GZSlab, GXSlab, SZTileLayout>{};
    launch_tiled_sympow_kernel<duplicate_correction>(mos, Z, X);
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
    def from_args(cls, Z, X, power, d_tile, duplicate_correction, b_tile, ZFrgShape, SZTileLayout):
        assert Z.dtype == X.dtype
        dtype = Z.dtype
        bs, d, D = problem_dimensions(Z.shape, X.shape, power, d_tile)
        assert Z.shape == op_output_shape(X.shape, power, d_tile)
        return BindingCfg(d, bs, X.shape, Z.shape, X.stride(), Z.stride(),
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
        sc = SourceCode(
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
        return sc

def binding(Z, X, power, d_tile, duplicate_correction, b_tile, ZFrgShape, SZTileLayout):
    binding_cfg = BindingCfg.from_args(Z, X, power, d_tile, duplicate_correction, b_tile, ZFrgShape, SZTileLayout)
    jit(name = "sympow",
        code = str(binding_cfg.source),
    )(Z, X)


# ---------------------- Autotune --------------------------------

def reasonable_b_tiles(b):
    return [b_tile for b_tile in [1,4] if b_tile <= b and b % b_tile == 0]

def configurations(args: dict) -> list[dict]:
    Z, X, power, d_tile = args['Z'], args['X'], args['power'], args['d_tile']
    dtype = Z.dtype
    bs,d,D = problem_dimensions(Z.shape, X.shape, power, d_tile)
    configs = []
    for b_tile in reasonable_b_tiles(prod(bs)):
        for num_warp in [1,2,4]:
            SZTileLayout = Layout(Shape(Shape(*[Int(d_tile)]*power), Int(b_tile)))
            for b_frag in [b_frag for b_frag in [1,2,4] if b_tile % b_frag == 0]:
                for d_frag in [d_frag for d_frag in [1,2,4] if d_tile % d_frag == 0]:
                    configs.append({
                        'b_tile': b_tile,
                        'ZFrgShape': Shape(Shape(*[Int(d_frag)]*power), Int(b_frag)),
                        'SZTileLayout': SZTileLayout
                    })
    # Filter out configs that use too much SMEM
    smem_used = [c['SZTileLayout'].shape.size() * dtype_to_bytes(dtype) for c in configs]
    # TODO: if the kernel memory was allocated dynamically we could use 100% of the SMEM instead of 1/2
    configs = [c for c, smem in zip(configs, smem_used) if smem <= SMEM_LIMIT//2]
    return configs

def hash_fn(args: dict) -> str:
    Z, X, power, d_tile = args['Z'], args['X'], args['power'], args['d_tile']
    bs,d,D = problem_dimensions(Z.shape, X.shape, power, d_tile)
    return f"Z.shape={Z.shape}-X.shape={X.shape}-power={power}-d_tile={d_tile}-D={D}-d={d}"

cache = ConfigTimingCache('sympow', hash_fn)
binding_autotuned = pickbest(cache=cache, sweep=configurations, verbose=True, allow_failure=True)(binding)

