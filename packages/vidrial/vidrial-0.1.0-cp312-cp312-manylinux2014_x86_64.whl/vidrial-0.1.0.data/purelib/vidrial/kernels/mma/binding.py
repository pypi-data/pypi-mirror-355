from dataclasses import dataclass
from typing import Any
import torch as th
from vidrial.jit.mosaic_types.types import Shape, Layout, Int
from vidrial.jit.mosaic_types.util import layout_from_shape_stride, torch_dtype_to_c
from vidrial.jit.timingcache import ConfigTimingCache
from vidrial.jit.decorator import pickbest
from vidrial.jit.jit import jit, render
from vidrial.kernels.mma_configurator import base_configurator
from vidrial.kernels.mma.dimensions import problem_shape


# ------------------- Source Code -------------------

@dataclass
class SourceCode:
    T: str
    Atom: str
    MNKTileShape: Shape
    MNKAtomPlacement: Shape
    GASlab: Layout
    GBSlab: Layout
    GCSlab: Layout
    @property
    def template(self):
        return """
#include <cuda.h>
#include <cuda_runtime.h>
#include <iostream>
#include "cute/tensor.hpp"
#include "mma/kernel.cuh"
#include "mma_mosaic.cuh"

using namespace cute;
using namespace mosaic;

extern "C" void launch(void* __raw_A, void* __raw_B, void* __raw_C) {
    using T = {T};
    using Atom = MMA_Atom<{Atom}>;
    using MNKTileShape = decltype(static_tree_cast<int64_t>({MNKTileShape}{}));
    using MNKAtomPlacement = decltype(static_tree_cast<int64_t>({MNKAtomPlacement}{}));
    using GASlab = decltype(static_tree_cast<int64_t>({GASlab}{}));
    using GBSlab = decltype(static_tree_cast<int64_t>({GBSlab}{}));
    using GCSlab = decltype(static_tree_cast<int64_t>({GCSlab}{}));
    using Mosaic = MmaMosaic_sm80<T, Atom, MNKTileShape, MNKAtomPlacement, GASlab, GBSlab, GCSlab>;
    auto A = reinterpret_cast<T*>(__raw_A);
    auto B = reinterpret_cast<T*>(__raw_B);
    auto C = reinterpret_cast<T*>(__raw_C);
    launch_tiled_mma_kernel(Mosaic{}, A, B, C);
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
    A_shape: tuple[int, ...]
    B_shape: tuple[int, ...]
    C_shape: tuple[int, ...]
    A_stride: tuple[int, ...]
    B_stride: tuple[int, ...]
    C_stride: tuple[int, ...]
    Atom: str
    MNKTileShape: tuple[int, ...]
    MNKAtomPlacement: tuple[int, ...]
    smempipe: int
    regpipe: int
    use_ldsm: bool
    swizzle: int
    dtype: th.dtype
    @classmethod
    def from_args(cls, A, B, C, Atom, MNKTileShape, MNKAtomPlacement, smempipe, regpipe, use_ldsm, swizzle):
        assert A.dtype == B.dtype == C.dtype, f"Invalid {A.dtype}, {B.dtype}, {C.dtype}. Kernel currently assumes all input tensors have the same dtype"
        assert smempipe == 1, "currently only default smempipe is supported"
        assert regpipe == 1, "currently only default regpipe is supported"
        assert use_ldsm is True, "currently only default use_ldsm is supported"
        assert swizzle == 1, "currently only default swizzle is supported"  
        P, M, N, K = problem_shape(A.shape, B.shape, C.shape)
        return cls(P, M, N, K, A.shape, B.shape, C.shape, A.stride(), B.stride(), C.stride(), Atom, MNKTileShape, MNKAtomPlacement, smempipe, regpipe, use_ldsm, swizzle, A.dtype)
    @property
    def source(self):
        """ Conversion between the different variable name and shape conventions
                Python                        c++
            A_shape=[P,M,K]      ->      GASlabShape=[M,K,P]
            B_shape=[P,K,N]      ->      GBSlabShape=[N,K,P]
            C_shape=[P,M,N]      ->      GCSlabShape=[M,N,P]
        """
        GASlab = layout_from_shape_stride(self.A_shape, self.A_stride, (1, 2, 0))
        GBSlab = layout_from_shape_stride(self.B_shape, self.B_stride, (2, 1, 0))
        GCSlab = layout_from_shape_stride(self.C_shape, self.C_stride, (1, 2, 0))
        return SourceCode(
            T=torch_dtype_to_c(self.dtype),
            Atom=self.Atom,
            MNKTileShape=Shape(*[Int(x) for x in self.MNKTileShape]),
            MNKAtomPlacement=Shape(*[Int(x) for x in self.MNKAtomPlacement]),
            GASlab=GASlab,
            GBSlab=GBSlab,
            GCSlab=GCSlab,
        )

def binding(A, B, C, Atom, MNKTileShape, MNKAtomPlacement, smempipe, regpipe, use_ldsm, swizzle):
    binding_cfg = BindingCfg.from_args(A, B, C, Atom, MNKTileShape, MNKAtomPlacement, smempipe, regpipe, use_ldsm, swizzle)
    jit(name = "mma",
        code = str(binding_cfg.source)
    )(A, B, C)

# ---------------------- Autotune --------------------------------

def make_mma_configurator(smempipe=None, regpipe=None, use_ldsm=None, swizzle=None):
    def mma_configurator(args: dict) -> list[dict[str, Any]]:
        A, B, C = args['A'], args['B'], args['C']
        P, M, N, K = problem_shape(A.shape, B.shape, C.shape)
        return base_configurator(MNKP=(M, N, K, P), dtype=A.dtype, acc_dtype=th.float32, smempipe=smempipe, regpipe=regpipe, use_ldsm=use_ldsm, swizzle=swizzle)
    return mma_configurator

def hash_fn(args: dict) -> str:
    A, B, C = args['A'], args['B'], args['C']
    P, M, N, K = problem_shape(A.shape, B.shape, C.shape)
    A_major = 'K_major' if A.stride(-1) == 1 else 'M_major'
    B_major = 'N_major' if B.stride(-1) == 1 else 'K_major'
    C_major = 'N_major' if C.stride(-1) == 1 else 'M_major'
    return f"{A.dtype}-{B.dtype}-{C.dtype}-M_mod128_{M % 128}-N_mod128_{N % 128}-K_mod128_{K % 128}-{A_major}-{B_major}-{C_major}"

binding_autotuned = pickbest(cache=ConfigTimingCache('mma', hash_fn), sweep=make_mma_configurator(smempipe=1, regpipe=1, use_ldsm=True, swizzle=1), verbose=True, allow_failure=True)(binding)
