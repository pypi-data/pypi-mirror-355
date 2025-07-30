
#include <cuda.h>
#include <cuda_runtime.h>
#include <iostream>
#include "cute/tensor.hpp"
#include "mma_sympow_bwd/kernel.cuh"
using namespace cute;
using namespace mosaic;
extern "C" void launch(void* __raw_A, void* __raw_B, void* __raw_c, void* __raw_c_dot) {
    using T = bfloat16_t;
    using MNKPSlabShape = decltype(static_tree_cast<int64_t>(Shape<Int<2304>, Int<1024>, Int<64>, Int<8>>{}));
    using MNKTileShape = decltype(static_tree_cast<int64_t>(Shape<Int<64>, Int<64>, Int<64>>{}));
    constexpr int d = 64, d_tile = 8;
    constexpr int pow = 2;
    constexpr int expand_dim = -2;
    using GASlab = decltype(static_tree_cast<int64_t>(Layout<Shape<Int<2304>, Int<64>, Int<8>>, Stride<Int<64>, Int<1>, Int<147456>>>{}));
    using GBSlab = decltype(static_tree_cast<int64_t>(Layout<Shape<Int<1024>, Int<64>, Int<8>>, Stride<Int<64>, Int<1>, Int<65536>>>{}));
    using GcSlab = decltype(static_tree_cast<int64_t>(Layout<Shape<Int<64>, Int<1024>, Int<8>>, Stride<Int<1024>, Int<1>, Int<65536>>>{}));
    constexpr bool duplicate_correction = true;
    using PerfMosaic = PerfMosaic<2, 1, true, 1>;
    using Atom = MMA_Atom<SM80_16x8x16_F32BF16BF16F32_TN>;
    using MNKAtomPlacement = decltype(static_tree_cast<int64_t>(Shape<Int<4>, Int<1>, Int<1>>{}));
    using Mosaic = SympowCMmaMosaic<T, pow, Atom, MNKAtomPlacement, MNKPSlabShape, MNKTileShape, d, d_tile, GASlab, GBSlab, GcSlab>;
    auto A = reinterpret_cast<T*>(__raw_A);
    auto B = reinterpret_cast<T*>(__raw_B);
    auto c = reinterpret_cast<T*>(__raw_c);
    auto c_dot = reinterpret_cast<T*>(__raw_c_dot);
    launch_mma_sympow_bwd_kernel<duplicate_correction>(Mosaic{}, A, B, c, c_dot);
}
