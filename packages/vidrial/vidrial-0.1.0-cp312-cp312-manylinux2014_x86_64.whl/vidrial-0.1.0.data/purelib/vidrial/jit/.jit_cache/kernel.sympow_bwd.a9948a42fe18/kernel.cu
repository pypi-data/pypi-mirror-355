
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
    using T = bfloat16_t;
    auto X = reinterpret_cast<T*>(__raw_X);
    auto Zgrad = reinterpret_cast<T*>(__raw_Zgrad);
    auto Xgrad = reinterpret_cast<T*>(__raw_Xgrad);
    using GXSlab = Layout<Shape<Int<64>, Shape<Int<16>, Int<1024>>>, Stride<Int<1>, Stride<Int<65536>, Int<64>>>>;
    using GZSlab = Layout<Shape<Shape<Shape<Int<8>, Int<8>>, Int<36>>, Shape<Int<16>, Int<1024>>>, Stride<Stride<Stride<Int<1>, Int<8>>, Int<64>>, Stride<Int<2359296>, Int<2304>>>>;
    constexpr int p = 2;
    constexpr int d_tile = 8;
    constexpr int b_tile = 4;
    using ZFrgShape = Shape<Shape<Int<1>, Int<1>>, Int<4>>;
    constexpr bool duplicate_correction = true;
    using XSlabShape = Shape<Int<64>, Shape<Int<16>, Int<1024>>>;
    using ZSlabShape = decltype(sympow_shape<p, d_tile>(XSlabShape{}));
    using XTileShape = Shape<Int<d_tile>, Int<b_tile>>; 
    using ZTileShape = decltype(tpow_shape<p>(XTileShape{}));
    using SZTileLayout = Layout<Shape<Shape<Int<8>, Int<8>>, Int<4>>, Stride<Stride<Int<1>, Int<8>>, Int<64>>>;
    using ZFrgThr = decltype(zipped_divide(Layout<ZTileShape>{}, ZFrgShape{}));
    auto mos = SympowMosaic<T, p, XSlabShape, XTileShape, ZFrgThr, GZSlab, GXSlab, SZTileLayout>{};
    launch_tiled_sympow_bwd_kernel<duplicate_correction>(mos, X, Zgrad, Xgrad);
}
