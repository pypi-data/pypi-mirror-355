
#include <cuda.h>
#include <cuda_runtime.h>
#include <iostream>
#include "cute/tensor.hpp"
#include "sympow_mma/kernel.cuh"

using namespace cute;
using namespace mosaic;

extern "C" void launch(void* __raw_A, void* __raw_B, void* __raw_C) {
    using T = bfloat16_t;
    using MNKPSlabShape = decltype(static_tree_cast<int64_t>(Shape<Int<4096>, Int<64>, Int<2304>, Int<4>>{}));
    using MNKTileShape = decltype(static_tree_cast<int64_t>(Shape<Int<128>, Int<16>, Int<64>>{}));
    constexpr int d = 64, d_tile = 8;
    constexpr int pow = 2;
    constexpr bool expand_K = true;
    using GaSlab = decltype(static_tree_cast<int64_t>(Layout<Shape<Int<4096>, Int<64>, Int<4>>, Stride<Int<64>, Int<1>, Int<262144>>>{}));
    using GBSlab = decltype(static_tree_cast<int64_t>(Layout<Shape<Int<64>, Int<2304>, Int<4>>, Stride<Int<1>, Int<64>, Int<147456>>>{}));
    using GCSlab = decltype(static_tree_cast<int64_t>(Layout<Shape<Int<4096>, Int<64>, Int<4>>, Stride<Int<64>, Int<1>, Int<262144>>>{}));
    constexpr bool duplicate_correction = true;
    using PerfMosaic = PerfMosaic<1, 1, true, 1>;
    using Atom = MMA_Atom<SM80_16x8x16_F32BF16BF16F32_TN>;
    using MNKAtomPlacement = decltype(static_tree_cast<int64_t>(Shape<Int<2>, Int<2>, Int<1>>{}));
    using Mosaic = SympowMmaMosaic<T, pow, Atom, MNKAtomPlacement, MNKPSlabShape, MNKTileShape, d, d_tile, expand_K, GaSlab, GBSlab, GCSlab, PerfMosaic>;
    auto A = reinterpret_cast<T*>(__raw_A);
    auto B = reinterpret_cast<T*>(__raw_B);
    auto C = reinterpret_cast<T*>(__raw_C);
    launch_sympow_mma_kernel<duplicate_correction>(Mosaic{}, A, B, C);
}