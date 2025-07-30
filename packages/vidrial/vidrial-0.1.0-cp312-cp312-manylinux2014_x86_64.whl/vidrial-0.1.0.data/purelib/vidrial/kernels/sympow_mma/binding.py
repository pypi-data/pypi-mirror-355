from typing import Dict, Any
from dataclasses import dataclass
from math import prod
import torch as th
from vidrial.jit.mosaic_types.types import Shape, Layout, Int
from vidrial.jit.mosaic_types.util import layout_from_shape_stride, torch_dtype_to_c
from vidrial.mosaic.utils.common import diff
from vidrial.kernels.mma_configurator import advanced_configurator
from vidrial.jit.timingcache import ConfigTimingCache
from vidrial.jit.decorator import pickbest
from vidrial.jit.jit import jit, render
from vidrial.kernels.sympow_mma.dimensions import problem_shape


# ------------------- Source Code -------------------

@dataclass
class SourceCode:
    T: str
    MNKPSlabShape: Shape
    MNKTileShape: Shape
    d: int
    d_tile: int
    pow: int
    expand_K: bool
    GaSlab: Layout
    GBSlab: Layout
    GCSlab: Layout
    duplicate_correction: bool
    smempipe: int
    regpipe: int
    use_ldsm: bool
    swizzle: int
    Atom: str
    MNKAtomPlacement: Shape
    @property
    def template(self):
        return """
#include <cuda.h>
#include <cuda_runtime.h>
#include <iostream>
#include "cute/tensor.hpp"
#include "sympow_mma/kernel.cuh"

using namespace cute;
using namespace mosaic;

extern "C" void launch(void* __raw_A, void* __raw_B, void* __raw_C) {
    using T = {T};
    using MNKPSlabShape = decltype(static_tree_cast<int64_t>({MNKPSlabShape}{}));
    using MNKTileShape = decltype(static_tree_cast<int64_t>({MNKTileShape}{}));
    constexpr int d = {d}, d_tile = {d_tile};
    constexpr int pow = {pow};
    constexpr bool expand_K = {expand_K};
    using GaSlab = decltype(static_tree_cast<int64_t>({GaSlab}{}));
    using GBSlab = decltype(static_tree_cast<int64_t>({GBSlab}{}));
    using GCSlab = decltype(static_tree_cast<int64_t>({GCSlab}{}));
    constexpr bool duplicate_correction = {duplicate_correction};
    using PerfMosaic = PerfMosaic<{smempipe}, {regpipe}, {use_ldsm}, {swizzle}>;
    using Atom = MMA_Atom<{Atom}>;
    using MNKAtomPlacement = decltype(static_tree_cast<int64_t>({MNKAtomPlacement}{}));
    using Mosaic = SympowMmaMosaic<T, pow, Atom, MNKAtomPlacement, MNKPSlabShape, MNKTileShape, d, d_tile, expand_K, GaSlab, GBSlab, GCSlab, PerfMosaic>;
    auto A = reinterpret_cast<T*>(__raw_A);
    auto B = reinterpret_cast<T*>(__raw_B);
    auto C = reinterpret_cast<T*>(__raw_C);
    launch_sympow_mma_kernel<duplicate_correction>(Mosaic{}, A, B, C);
}"""
    def __str__(self):
        return render(self.template, self.__dict__)


# ------------------- Binding -------------------

@dataclass
class BindingCfg:
    P: int # batch dimension
    M: int
    N: int
    K: int
    d: int
    d_tile: int
    pow: int
    expand_dim: int 
    A_shape: tuple[int, ...]
    B_shape: tuple[int, ...]
    C_shape: tuple[int, ...]
    A_stride: tuple[int, ...]
    B_stride: tuple[int, ...]
    C_stride: tuple[int, ...]
    duplicate_correction: bool
    smempipe: int
    regpipe: int
    use_ldsm: bool
    swizzle: int
    Atom: str
    MNKTileShape: Shape 
    MNKAtomPlacement: Shape
    dtype: th.dtype
    @classmethod
    def from_args(cls, A: th.Tensor, B: th.Tensor, C: th.Tensor, expand_dim: int, power: int, d_tile: int, duplicate_correction: bool,
                  smempipe: int, regpipe: int, use_ldsm: bool, swizzle: int, Atom: str, MNKTileShape: Shape, MNKAtomPlacement: Shape) -> 'BindingCfg':
        assert A.dtype == B.dtype == C.dtype, f"Invalid {A.dtype}, {B.dtype}, {C.dtype}. Kernel currently assumes all input tensors have the same dtype"
        dtype = A.dtype
        P, M, N, K, d, D = problem_shape(A.shape, B.shape, C.shape, expand_dim, power, d_tile)
        return cls(P=P, M=M, N=N, K=K, d=d, d_tile=d_tile, pow=power, expand_dim=expand_dim, duplicate_correction=duplicate_correction, 
                   A_shape=A.shape, B_shape=B.shape, C_shape=C.shape,
                   A_stride=A.stride(), B_stride=B.stride(), C_stride=C.stride(),
                   smempipe=smempipe, regpipe=regpipe, use_ldsm=use_ldsm, swizzle=swizzle,
                   Atom=Atom, MNKTileShape=MNKTileShape, MNKAtomPlacement=MNKAtomPlacement, dtype=dtype)
    @property
    def source(self):
        """ Conversion between the different variable name and shape conventions
                     Python                       c++
                A                    ->      a
                eA                   ->      A
                A_shape=[P,M,d]      ->      aSlabShape=[M,d,P]    if expand_K
                A_shape=[P,d,K]      ->      aSlabShape=[d,K,P]    if not expand_K
                B_shape=[P,K,N]      ->      BSlabShape=[N,K,P]
                C_shape=[P,M,N]      ->      CSlabShape=[M,N,P]
        """
        return SourceCode(
            T=torch_dtype_to_c(self.dtype),
            MNKPSlabShape=Shape(Int(self.M), Int(self.N), Int(self.K), Int(self.P)),
            d=self.d,
            d_tile=self.d_tile,
            pow=self.pow,
            expand_K=True if self.expand_dim%3 == 2 else False,
            GaSlab=layout_from_shape_stride(self.A_shape, self.A_stride, (1, 2, 0)),
            GBSlab=layout_from_shape_stride(self.B_shape, self.B_stride, (2, 1, 0)),
            GCSlab=layout_from_shape_stride(self.C_shape, self.C_stride, (1, 2, 0)),
            duplicate_correction=self.duplicate_correction,
            smempipe=self.smempipe,
            regpipe=self.regpipe,
            use_ldsm=self.use_ldsm,
            swizzle=self.swizzle,
            Atom=self.Atom,
            MNKTileShape=self.MNKTileShape,
            MNKAtomPlacement=self.MNKAtomPlacement)

def binding(A, B, C, expand_dim, power, d_tile, duplicate_correction, smempipe, regpipe, use_ldsm, swizzle, Atom, MNKTileShape, MNKAtomPlacement):
    binding_cfg = BindingCfg.from_args(A, B, C, expand_dim, power, d_tile, duplicate_correction, smempipe, regpipe, use_ldsm, swizzle, Atom, MNKTileShape, MNKAtomPlacement)
    jit(name = "sympow_mma",
        code = str(binding_cfg.source)
    )(A, B, C)


# ---------------------- Autotune --------------------------------

def make_configurator(smempipe: tuple[int, int], regpipe: tuple[int, int], use_ldsm: bool, swizzle: int):
    def configurator(args: dict) -> list[Dict[str, Any]]:
        A, B, C, expand_dim, power, d_tile, duplicate_correction = args['A'], args['B'], args['C'], args['expand_dim'], args['power'], args['d_tile'], args['duplicate_correction']
        P, M, N, K, d, D = problem_shape(A.shape, B.shape, C.shape, expand_dim, power, d_tile)
        D_tile = d_tile ** power
        if expand_dim % 3 == 2: # expand K
            M_tile, N_tile, K_tile = None, None, D_tile 
        else: # expand M
            M_tile, N_tile, K_tile = D_tile, None, None
        configs = advanced_configurator((M, N, K, P), A.dtype, th.float32, M_tile, N_tile, K_tile, smempipe=smempipe, regpipe=regpipe, use_ldsm=use_ldsm, swizzle=swizzle)
        return configs
    return configurator

def hash_fn(args: dict) -> str:
    P, M, N, K, d, D = problem_shape(args['A'].shape, args['B'].shape, args['C'].shape, args['expand_dim'], args['power'], args['d_tile'])
    A, B, C = args['A'], args['B'], args['C']
    A_major = 'K_major' if A.stride(-1) == 1 else 'M_major'
    B_major = 'N_major' if B.stride(-1) == 1 else 'K_major'
    C_major = 'N_major' if C.stride(-1) == 1 else 'M_major'
    expand_dim = args['expand_dim'] % 3
    return f"{A.dtype}-{B.dtype}-{C.dtype}-M_mod128_{M % 128}-N_mod128_{N % 128}-K_mod128_{K % 128}-{A_major}-{B_major}-{C_major}-{expand_dim}-{args['power']}-{args['d_tile']}"

binding_autotuned = pickbest(cache=ConfigTimingCache('sympow_mma', hash_fn), sweep=make_configurator(smempipe=(1,2), regpipe=(0,1), use_ldsm=True, swizzle=1), verbose=True, allow_failure=True)(binding)
