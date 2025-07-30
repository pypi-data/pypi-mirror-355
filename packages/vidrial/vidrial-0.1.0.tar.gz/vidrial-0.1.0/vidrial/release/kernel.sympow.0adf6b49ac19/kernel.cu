
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
    using T = bfloat16_t;
    auto Z = reinterpret_cast<T*>(__raw_Z);
    auto X = reinterpret_cast<T*>(__raw_X);
    using XSlabShape = Shape<Int<64>, Shape<Int<128>, Int<4096>>>;
    using GXSlab = decltype(static_tree_cast<int64_t>(Layout<Shape<Int<64>, Shape<Int<128>, Int<4096>>>, Stride<Int<4096>, Stride<Int<262144>, Int<1>>>>{}));
    using GZSlab = decltype(static_tree_cast<int64_t>(Layout<Shape<Shape<Shape<Int<8>, Int<8>>, Int<36>>, Shape<Int<128>, Int<4096>>>, Stride<Stride<Stride<Int<1>, Int<8>>, Int<64>>, Stride<Int<9437184>, Int<2304>>>>{}));
    constexpr int p = 2;
    constexpr int d_tile = 8;
    constexpr int b_tile = 4;
    using ZFrgShape = Shape<Shape<Int<2>, Int<2>>, Int<4>>;
    constexpr bool duplicate_correction = true;
    using ZSlabShape = decltype(sympow_shape<p, d_tile>(XSlabShape{}));
    using XTileShape = Shape<Int<d_tile>, Int<b_tile>>; 
    using ZTileShape = decltype(tpow_shape<p>(XTileShape{}));
    using SZTileLayout = Layout<Shape<Shape<Int<8>, Int<8>>, Int<4>>, Stride<Stride<Int<1>, Int<8>>, Int<64>>>;
    using ZFrgThr = decltype(zipped_divide(Layout<ZTileShape>{}, ZFrgShape{}));
    auto mos = SympowMosaic<T, p, XSlabShape, XTileShape, ZFrgThr, GZSlab, GXSlab, SZTileLayout>{};
    launch_tiled_sympow_kernel<duplicate_correction>(mos, Z, X);
}
    