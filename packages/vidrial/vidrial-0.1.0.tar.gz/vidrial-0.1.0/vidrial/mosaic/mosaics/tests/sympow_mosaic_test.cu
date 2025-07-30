#include <gtest/gtest.h>
#include "sympow_mosaic.cuh"
#include "kernels/sympow/kernel.cuh"

namespace mosaic {
namespace {

/* These tests compare the outputs of the sympow_kernel with the single threaded sympow implementation */
template<typename T, int p, typename XSlabShape, typename Params>
void test_sympow(XSlabShape X_slab_shape, Params params) {
    constexpr bool duplicate_correction = false;
    using XTileShape = typename Params::XTileShape;
    using ZTileLayout = typename Params::ZTileLayout;
    using ZFrgShape = typename Params::ZFrgShape;
    using ZFrgThr = typename Params::ZFrgThr;
    static constexpr int d_blk = get<0>(XTileShape{});
    auto Z_slab_shape = sympow_shape<p, d_blk>(X_slab_shape);
    using XSlab = Layout<XSlabShape>;
    using ZSlab = Layout<decltype(Z_slab_shape)>;
    auto mos = SympowMosaic<T, p, XSlabShape, XTileShape, ZFrgThr, ZSlab, XSlab, ZTileLayout>{};
    auto gX = make_managed_tensor<T>(XSlab{});
    auto gZ = make_managed_tensor<T>(ZSlab{});
    auto gZ_ref = make_managed_tensor<T>(ZSlab{});
    for (int i = 0; i < size(gX); ++i) gX(i) = static_cast<T>(i%19);
    int blocks = size<1,1>(mos.Y.TileBlock);
    { // no duplicate correction
        tiled_sympow_kernel<false><<<blocks, mos.thread_num>>>(mos, gZ.data(), gX.data());
        CHECK_CUDA();
        sympow<p, d_blk, false>(gZ_ref, gX);
        ASSERT_TRUE(check_tensors_match(gZ, gZ_ref, 0., false));
    }{ // duplicate correction
        clear(gZ); clear(gZ_ref);
        tiled_sympow_kernel<true><<<blocks, mos.thread_num>>>(mos, gZ.data(), gX.data());
        CHECK_CUDA();
        sympow<p, d_blk, true>(gZ_ref, gX);
        ASSERT_TRUE(check_tensors_match(gZ, gZ_ref, 0., false));
    }
}

TEST(SympowMosaic, SimpleP2) {
    constexpr int p = 2;
    struct Params {
        using XTileShape = Shape<_8,_8>;
        using ZTileLayout = Layout<decltype(tpow_shape<p>(XTileShape{}))>;
        using ZFrgShape = Shape<Shape<_4, _4>, _1>;
        using ZFrgThr = decltype(zipped_divide(ZTileLayout{}, ZFrgShape{}));
    };
    test_sympow<float, 2>(make_shape(_16{},_16{}), Params{});
}
TEST(SympowMosaic, SimpleP3) {
    constexpr int p = 3;
    struct Params {
        using XTileShape = Shape<_8,_8>;
        using ZTileLayout = Layout<decltype(tpow_shape<p>(XTileShape{}))>;
        using ZFrgShape = Shape<Shape<_4, _4, _2>, _1>;
        using ZFrgThr = decltype(zipped_divide(ZTileLayout{}, ZFrgShape{}));
    };
    test_sympow<float, p>(make_shape(_16{},_16{}), Params{});
}
TEST(SympowMosaic, SimpleP4) {
    constexpr int p = 4;
    struct Params {
        using XTileShape = Shape<_4,_2>;
        using ZTileLayout = Layout<decltype(tpow_shape<p>(XTileShape{}))>;
        using ZFrgShape = Shape<Shape<_4, _4, _2, _1>, _1>;
        using ZFrgThr = decltype(zipped_divide(ZTileLayout{}, ZFrgShape{}));
    };
    test_sympow<float, p>(make_shape(_16{},_16{}), Params{});
}

struct tile8x8x8_frg4x4x1_basic {
    using XTileShape = Shape<_8,_8>;
    using ZTileShape = decltype(tprod_shape(XTileShape{}, XTileShape{}));
    using ZTileLayout = Layout<ZTileShape>;
    using ZFrgShape = Shape<Shape<_4, _4>, _1>;
    using ZFrgThr = decltype(zipped_divide(make_layout(ZTileShape{}), ZFrgShape{}));
};
struct tile8x8x8_frg4x4x1 {
    using XTileShape = Shape<_8,_8>;
    using ZTileShape = decltype(tprod_shape(XTileShape{}, XTileShape{}));
    using ZTileLayout = Layout<Shape<Shape<Shape<_4,_2>,Shape<_2,_2,_2>>,_8>,
                              Stride<Stride<Stride<_1,_64>,Stride<_128,_4,_256>>,_8>>;
    using ZFrgShape = Shape<Shape<_4, _4>, _1>;
    using ZFrgThr = Layout<Shape<Shape<Shape<Shape<_2,_2>,Shape<_2,_2>>,_1>,
                                Shape<_2,_2,_8>>,
                          Stride<Stride<Stride<Stride<_1,_4>,Stride<_8,_32>>,_0>,
                                 Stride<_2,_16,_64>>>;
};
struct tile8x8x32_frg8x8x1 {
    using XTileShape = Shape<_8,_8>;
    using ZTileShape = decltype(tprod_shape(XTileShape{}, XTileShape{}));
    using ZTileLayout = Layout<Shape<Shape<_8,_8>,_32>,
                              Stride<Stride<_32,_256>,_1>>;
    using ZFrgShape = Shape<Shape<_8, _8>, _1>;
    using ZFrgThr = decltype(zipped_divide(make_layout(ZTileShape{}), ZFrgShape{}));
};
TEST(SympowMosaic, X16x16_TestDifferentSmemLayouts) {
    using T = float;
    auto X_slab_shape = make_shape(_16{},_16{});
    test_sympow<T,2>(X_slab_shape, tile8x8x8_frg4x4x1_basic{});
    test_sympow<T,2>(X_slab_shape, tile8x8x8_frg4x4x1{});
    test_sympow<T,2>(X_slab_shape, tile8x8x32_frg8x8x1{});
}
TEST(SympowMosaic, half_t_X16x16_TestDifferentSmemLayouts) {
    using T = half_t;
    auto X_slab_shape = make_shape(_16{},_16{});
    test_sympow<T,2>(X_slab_shape, tile8x8x8_frg4x4x1_basic{});
    test_sympow<T,2>(X_slab_shape, tile8x8x8_frg4x4x1{});
    test_sympow<T,2>(X_slab_shape, tile8x8x32_frg8x8x1{});
}
TEST(SympowMosaic, X64x32_TestDifferentSmemLayouts) {
    using T = float;
    auto X_slab_shape = make_shape(_64{},_32{});
    test_sympow<T,2>(X_slab_shape, tile8x8x8_frg4x4x1_basic{});
    test_sympow<T,2>(X_slab_shape, tile8x8x8_frg4x4x1{});
    test_sympow<T,2>(X_slab_shape, tile8x8x32_frg8x8x1{});
}
// Real problems might have multiple batch dimensions (for a transformer you might have batch, time, heads)
// You can pack them into a nested batch dimension and call the sympow kernel
TEST(SympowMosaic, NestedBatch) {
    struct nested_batch_params{
        using XTileShape = Shape<_8,Shape<_8,_1>>;
        using ZTileShape = decltype(tprod_shape(XTileShape{}, XTileShape{}));
        using ZTileLayout = Layout<ZTileShape>;
        using ZFrgShape = Shape<Shape<_4, _4>, _1>;
        using ZFrgThr = decltype(zipped_divide(make_layout(ZTileShape{}), ZFrgShape{}));
    };
    using T = half_t;
    auto X_slab_shape = make_shape(_64{},make_shape(_16{},_4{}));
    test_sympow<T,2>(X_slab_shape, nested_batch_params{});
}

}
}