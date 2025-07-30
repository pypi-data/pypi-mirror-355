from typing import Dict, Any
import torch as th
from dataclasses import dataclass
from vidrial.kernels.sympow.dimensions import sympow_dim
from vidrial.jit.mosaic_types.types import Shape, Layout, Int
from vidrial.jit.mosaic_types.util import layout_from_shape_stride, torch_dtype_to_c
from vidrial.kernels.mma_configurator import advanced_configurator
from vidrial.jit.jit import jit, render
from vidrial.jit.timingcache import ConfigTimingCache
from vidrial.jit.decorator import pickbest
from vidrial.kernels.mma_sympow_bwd.dimensions import canonical_inputs, dimensions

# ------------------- Source Code -------------------
@dataclass
class SourceCode:
    T: str
    MNKPSlabShape: Shape
    d: int
    d_tile: int
    pow: int
    GASlab: Layout
    GBSlab: Layout
    GcSlab: Layout
    duplicate_correction: bool
    MNKTileShape: Shape
    MNKAtomPlacement: Shape
    Atom: str
    smempipe: int
    regpipe: int
    use_ldsm: bool
    swizzle: bool
    @property
    def template(self):
        return """
#include <cuda.h>
#include <cuda_runtime.h>
#include <iostream>
#include "cute/tensor.hpp"
#include "mma_sympow_bwd/kernel.cuh"
using namespace cute;
using namespace mosaic;
extern "C" void launch(void* __raw_A, void* __raw_B, void* __raw_c, void* __raw_c_dot) {
    using T = {T};
    using MNKPSlabShape = decltype(static_tree_cast<int64_t>({MNKPSlabShape}{}));
    using MNKTileShape = decltype(static_tree_cast<int64_t>({MNKTileShape}{}));
    constexpr int d = {d}, d_tile = {d_tile};
    constexpr int pow = {pow};
    constexpr int expand_dim = -2;
    using GASlab = decltype(static_tree_cast<int64_t>({GASlab}{}));
    using GBSlab = decltype(static_tree_cast<int64_t>({GBSlab}{}));
    using GcSlab = decltype(static_tree_cast<int64_t>({GcSlab}{}));
    constexpr bool duplicate_correction = {duplicate_correction};
    using PerfMosaic = PerfMosaic<{smempipe}, {regpipe}, {use_ldsm}, {swizzle}>;
    using Atom = MMA_Atom<{Atom}>;
    using MNKAtomPlacement = decltype(static_tree_cast<int64_t>({MNKAtomPlacement}{}));
    using Mosaic = SympowCMmaMosaic<T, pow, Atom, MNKAtomPlacement, MNKPSlabShape, MNKTileShape, d, d_tile, GASlab, GBSlab, GcSlab>;
    auto A = reinterpret_cast<T*>(__raw_A);
    auto B = reinterpret_cast<T*>(__raw_B);
    auto c = reinterpret_cast<T*>(__raw_c);
    auto c_dot = reinterpret_cast<T*>(__raw_c_dot);
    launch_mma_sympow_bwd_kernel<duplicate_correction>(Mosaic{}, A, B, c, c_dot);
}
"""
    def __str__(self):
        return render(self.template, self.__dict__)

# ------------------- Binding -------------------
@dataclass
class BindingCfg:
    """ The main methods:
          from_args: constructs a BindingCfg with the binding arguments themselves
          source: the source code object that the binding relies upon
          canonical_args: preprocesses the arguments into the form accepted by the source code
    """
    M: int
    N: int
    K: int
    P: int
    d: int
    D: int
    dtype: th.dtype
    A_shape: tuple[int, ...]
    B_shape: tuple[int, ...]
    c_shape: tuple[int, ...]
    A_stride: tuple[int, ...]
    B_stride: tuple[int, ...]
    c_stride: tuple[int, ...]
    expand_dim: int  # TODO: Currently only expand_dim=-1 (D=N) is supported
    power: int
    d_tile: int
    duplicate_correction: bool
    MNKTileShape: Shape
    MNKAtomPlacement: Shape
    Atom: str
    smempipe: int
    regpipe: int
    use_ldsm: bool
    swizzle: bool
    @classmethod
    def from_args(cls, A, B, c, c_dot, expand_dim, power, d_tile, duplicate_correction, MNKTileShape, MNKAtomPlacement, Atom, smempipe, regpipe, use_ldsm, swizzle):
        assert A.dtype == B.dtype == c.dtype
        assert c.shape == c_dot.shape and c.stride() == c_dot.stride() and c.dtype == c_dot.dtype, "c and c_dot should have same shape, stride and dtype"
        dtype = A.dtype
        A, B, c, c_dot, expand_dim = canonical_inputs(A, B, c, c_dot, expand_dim)
        P, M, K, N, d = dimensions(A.shape, B.shape, c.shape, power, d_tile)
        D = sympow_dim(d, power, d_tile)
        assert M == D, f"N={N} must be equal to sympow_dim(d, power, d_tile)={D}"
        A_shape, B_shape, c_shape = tuple(A.shape), tuple(B.shape), tuple(c.shape)
        A_stride, B_stride, c_stride = A.stride(), B.stride(), c.stride()
        return cls(M, N, K, P, d, D, dtype,
                   A_shape, B_shape, c_shape, A_stride, B_stride, c_stride,
                   expand_dim, power, d_tile, duplicate_correction,
                   MNKTileShape, MNKAtomPlacement, Atom,
                   smempipe, regpipe, use_ldsm, swizzle)
    @property
    def source(self):
        """ Conversion between the different variable name and shape conventions
                M = D = sympow_dim(d, power, d_tile)
                    Python                     c++
                A_shape=[P,M,K]      ->      aSlabShape=[M,K,P]
                B_shape=[P,K,N]      ->      BSlabShape=[N,K,P]
                c_shape=[P,d,N]      ->      CSlabShape=[d,N,P]
        """
        return SourceCode(
            T=torch_dtype_to_c(self.dtype),
            MNKPSlabShape=Shape(Int(self.M), Int(self.N), Int(self.K), Int(self.P)),
            d=self.d,
            d_tile=self.d_tile,
            pow=self.power,
            GASlab=layout_from_shape_stride(self.A_shape, self.A_stride, (1, 2, 0)),
            GBSlab=layout_from_shape_stride(self.B_shape, self.B_stride, (2, 1, 0)),
            GcSlab=layout_from_shape_stride(self.c_shape, self.c_stride, (1, 2, 0)),
            duplicate_correction=self.duplicate_correction,
            MNKTileShape=self.MNKTileShape,
            MNKAtomPlacement=self.MNKAtomPlacement,
            Atom=self.Atom,
            smempipe=self.smempipe,
            regpipe=self.regpipe,
            use_ldsm=self.use_ldsm,
            swizzle=self.swizzle,
        )

def binding(A, B, c, c_dot, expand_dim, power, d_tile, duplicate_correction, MNKTileShape, MNKAtomPlacement, Atom, smempipe, regpipe, use_ldsm, swizzle):
    binding_cfg = BindingCfg.from_args(A, B, c, c_dot, expand_dim, power, d_tile, duplicate_correction, MNKTileShape, MNKAtomPlacement, Atom, smempipe, regpipe, use_ldsm, swizzle)
    jit(name = "mma_sympow_bwd",
        code = str(binding_cfg.source),
    )(A, B, c, c_dot)

# ------------------- Autotuned -------------------
# The functional arguments are A,B,c,c_dot,expand_dim,power,d_tile,duplicate_correction
# The rest are performance arguments MNKTileShape, MNKAtomPlacement, Atom, smempipe, regpipe, use_ldsm, swizzle
def make_configurator(smempipe: tuple[int, int], regpipe: tuple[int, int], use_ldsm: bool, swizzle: int):
    """ returns function that constCreates a set of promising configurations for the MMA kernel """
    def configurator(args: dict) -> list[Dict[str, Any]]:
        A, B, c, c_dot, expand_dim = canonical_inputs(args['A'], args['B'], args['c'], args['c_dot'], args['expand_dim'])
        P, M, K, N, d = dimensions(A.shape, B.shape, c.shape, args['power'], args['d_tile'])
        D_tile = args['d_tile'] ** args['power']
        configs = advanced_configurator((M, N, K, P), A.dtype, th.float32, D_tile, None, None, smempipe=smempipe, regpipe=regpipe, use_ldsm=use_ldsm, swizzle=swizzle)
        return configs
    return configurator


def hash_fn(args: dict) -> str:
    A, B, c, c_dot, expand_dim = canonical_inputs(args['A'], args['B'], args['c'], args['c_dot'], args['expand_dim'])
    M, N, K, d = A.shape[-2], B.shape[-2], B.shape[-1], c.shape[-2]
    return f"{A.dtype}-{B.dtype}-{c.dtype}-M_mod128_{M % 128}-N_mod128_{N % 128}-K_mod128_{K % 128}-d{d}-{expand_dim}-{args['power']}-{args['d_tile']}"

cache = ConfigTimingCache('mma_sympow_bwd', hash_fn)
autotuned = pickbest(cache=cache, sweep=make_configurator(smempipe=(1,2), regpipe=(0,1), use_ldsm=True, swizzle=1), verbose=True, allow_failure=True)(binding)

