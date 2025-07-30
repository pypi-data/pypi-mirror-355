#include <gtest/gtest.h>
#include "copy_mosaic.cuh"
#include "copy_kernels.cuh"
#include "utilities.cuh"

namespace mosaic {
namespace {

TEST(ElementTest, Shp_8x8) {
    using Shp = Shape<_8, _8>;
    { // Share 2 contiguous elements
        using A = Layout<Shape<_8, _8>>;
        using B = Layout<Shape<Shape<_2,_4>,_8>,
                        Stride<Stride<_1,_16>,_2>>;
        auto ref_elements = Layout<Shape<_2,Shape<_4,_8>>,
                                Stride<_1,Stride<_2,_8>>>{};
        auto elements_AB = break_into_elements<Shp, A, B, 128>();
        auto elements_BA = break_into_elements<Shp, B, A, 128>();
        ASSERT_EQ(elements_AB, ref_elements);
        ASSERT_EQ(elements_BA, ref_elements);
    }{ // both rows are contiguous
        using A = Layout<Shape<_8,_8>,Stride<_8,_1>>;
        using B = Layout<Shape<_8,_8>,Stride<_8,_1>>;
        auto ref_elements = Layout<Shape<_8,Shape<_8,_1>>,
                                Stride<_8,Stride<_1,_0>>>{};
        auto elements_AB = break_into_elements<Shp, A, B, 128>();
        auto elements_BA = break_into_elements<Shp, B, A, 128>();
        ASSERT_EQ(elements_AB, ref_elements);
        ASSERT_EQ(elements_BA, ref_elements);
    }{ // both rows are contiguous, max_shar_size < row_size
        using A = Layout<Shape<_8,_8>,Stride<_8,_1>>;
        using B = Layout<Shape<_8,_8>,Stride<_8,_1>>;
        auto ref_elements = Layout<Shape<_4,Shape<_8,_2>>,
                                Stride<_8,Stride<_1,_32>>>{};
        auto elements_AB = break_into_elements<Shp, A, B, 4>();
        auto elements_BA = break_into_elements<Shp, B, A, 4>();
        ASSERT_EQ(elements_AB, ref_elements);
        ASSERT_EQ(elements_BA, ref_elements);
    }{ // Contiguous along different modes of the shape
        using A = Layout<Shape<_8,_8>>;
        using B = Layout<Shape<_8,_8>,Stride<_8,_1>>;
        auto ref_elements = Layout<Shape<_1,Shape<_8,_8>>,
                                Stride<_1,Stride<_1,_8>>>{};
        auto elements_AB = break_into_elements<Shp, A, B, 128>();
        auto elements_BA = break_into_elements<Shp, B, A, 128>();
        ASSERT_EQ(elements_AB, ref_elements);
        ASSERT_EQ(elements_BA, ref_elements);
    }{ // Non-contiguous layout
        using A = Layout<Shape<_8,_8>,Stride<_2,_32>>;
        using B = Layout<Shape<_8,_8>,Stride<_8,_1>>;
        auto ref_elements = Layout<Shape<_1,Shape<_8,_8>>,
                                Stride<_0,Stride<_1,_8>>>{};
        auto elements_AB = break_into_elements<Shp, A, B, 128>();
        auto elements_BA = break_into_elements<Shp, B, A, 128>();
        ASSERT_EQ(elements_AB, ref_elements);
        ASSERT_EQ(elements_BA, ref_elements);
    }{ // Contiguous but not compact
        using A = Layout<Shape<_8,_8>,Stride<_1,_32>>;
        using B = Layout<Shape<_8,_8>,Stride<_1,_8>>;
        auto ref_elements = Layout<Shape<_8,Shape<_1,_8>>,
                                Stride<_1,Stride<_0,_8>>>{};
        auto elements_AB = break_into_elements<Shp, A, B, 128>();
        auto elements_BA = break_into_elements<Shp, B, A, 128>();
        ASSERT_EQ(elements_AB, ref_elements);
        ASSERT_EQ(elements_BA, ref_elements);
    }
}

TEST(MaximallyContiguousFrgThr, Shp64x64_row) {
    using AShape = Shape<_64,_64>;
    using A = Layout<AShape,Stride<_64,_1>>;
    auto FrgThr = maximally_contiguous_FrgThr<32, 8, AShape>(A{}, A{});
    auto correct_FrgThr = Layout<Shape<Shape<_8,_16,_1>,Shape<_8,_4>>,
                                  Stride<Stride<_64,_4,_0>,Stride<_512,_1>>>{};
    ASSERT_EQ(FrgThr, correct_FrgThr);
}

TEST(MaximallyContiguousFrgThr, Shp16x32x64_order_210) {
    using AShape = Shape<_16,_32,_64>;
    using A = Layout<AShape,Stride<_2048,_64,_1>>;
    constexpr int max_frag_size = 16;
    constexpr int thread_num = 128;
    auto FrgThr = maximally_contiguous_FrgThr<thread_num, max_frag_size, AShape>(A{}, A{});
    auto correct_FrgThr = Layout<Shape<Shape<_16,_16,_1,_1>,Shape<_4,_32>>,
                                  Stride<Stride<_512,_1,_0,_0>,Stride<_8192,_16>>>{};
    ASSERT_EQ(FrgThr, correct_FrgThr);
}

TEST(MaximallyContiguousFrgThr, Shp64x32x16_row) {
    using AShape = Shape<_64,_64>;
    using A = Layout<AShape,Stride<_64,_1>>;
    auto FrgThr = maximally_contiguous_FrgThr<32, 8, AShape>(A{}, A{});
    auto correct_FrgThr = Layout<Shape<Shape<_8,_16,_1>,Shape<_8,_4>>,
                                  Stride<Stride<_64,_4,_0>,Stride<_512,_1>>>{};
    ASSERT_EQ(FrgThr, correct_FrgThr);
}

TEST(MaximallyContiguousFrgThr, Shp64x64_col) {
    using AShape = Shape<_64,_64>;
    using A = Layout<AShape,Stride<_1,_64>>;
    auto FrgThr = maximally_contiguous_FrgThr<32, 8, AShape>(A{}, A{});
    auto correct_FrgThr = Layout<Shape<Shape<_8,_1,_16>,_32>,
                                  Stride<Stride<_1,_0,_256>,_8>>{};
    ASSERT_EQ(FrgThr, correct_FrgThr);
}

TEST(MaximallyContiguousFrgThr, Shp16x32x64_col) {
    using AShape = Shape<_16,_32,_64>;
    using A = Layout<AShape,Stride<_1,_16,_512>>;
    auto FrgThr = maximally_contiguous_FrgThr<32, 8, AShape>(A{}, A{});
    auto correct_FrgThr = Layout<Shape<Shape<_8,_1,_2,_64>,_32>,
                                  Stride<Stride<_1,_0,_256,_512>,_8>>{};
    ASSERT_EQ(FrgThr, correct_FrgThr);
}

TEST(MaximallyContiguousFrgThr, Shp16x_32x64_row) {
    using AShape = Shape<_16,Shape<_32,_64>>;
    using A = Layout<AShape,Stride<_2048,Stride<_64,_1>>>;
    auto FrgThr = maximally_contiguous_FrgThr<32, 8, AShape>(A{}, A{});
    auto correct_FrgThr = Layout<Shape<Shape<_8,_16,Shape<_8,_1>>,Shape<_8,_4>>,
                                 Stride<Stride<_512,_1,Stride<_64,_0>>,Stride<_4096,_16>>>{};
    ASSERT_EQ(FrgThr, correct_FrgThr);
}

TEST(MaximallyContiguousFrgThr, Shp32x16_col) {
    using AShape = Shape<_32,_16>;
    using A = Layout<AShape,Stride<_1,_32>>;
    auto FrgThr = maximally_contiguous_FrgThr<32, 8, AShape>(A{}, A{});
    auto correct_FrgThr = Layout<Shape<Shape<_8,_1,_2>,_32>,
                                  Stride<Stride<_1,_0,_256>,_8>>{};
    ASSERT_EQ(FrgThr, correct_FrgThr);
}

TEST(CopyMosaicTest, AddOne) {
    using M = Int<8>; using N = Int<8>;
    using A = Layout<Shape<M, N>>;
    using TileShape = Shape<_8,_8>;
    auto mosaic = make_tiling_mosaic<float, 32>(A{}.shape(), TileShape{}, A{});
    auto gA = make_managed_tensor<float>(A{});
    for (int i = 0; i < size(gA); i++) { gA(i) = i; }
    int blocks = size<1>(mosaic.TileBlock);
    tensor_scalar_add_kernel<<<blocks, int(mosaic.thread_num)>>>(mosaic, gA.data(), gA.data(), 1.f);
    cudaDeviceSynchronize();
    auto gA_ref = make_managed_tensor<float>(A{});
    for (int i = 0; i < size(gA); i++) { gA_ref(i) = i+1; }
    bool match = check_tensors_match(gA, gA_ref, 0., false);
    ASSERT_TRUE(match);
}

TEST(CopyMosaicTest, AddOne_gColMaj_sRowMaj) {
    using M = Int<32>; using N = Int<32>;
    using ASlab = Layout<Shape<M, N>>;
    using TileShape = Shape<_16,_16>;
    using STile = Layout<Shape<_16,_16>, Stride<_16,_1>>;
    auto mosaic = make_tiling_mosaic<float, 32>(ASlab{}.shape(), TileShape{}, ASlab{}, STile{});
    auto gA = make_managed_tensor<float>(ASlab{});
    for (int i = 0; i < size(gA); i++) { gA(i) = i; }
    int blocks = size<1>(mosaic.TileBlock);
    tensor_scalar_add_kernel<<<blocks, int(mosaic.thread_num)>>>(mosaic, gA.data(), gA.data(), 1.f);
    cudaDeviceSynchronize();
    auto gA_ref = make_managed_tensor<float>(ASlab{});
    for (int i = 0; i < size(gA); i++) { gA_ref(i) = i+1; }
    bool match = check_tensors_match(gA, gA_ref, 0., false);
    ASSERT_TRUE(match);
}

TEST(CopyMosaicTest, SimpleMove) {
    using GSlab= decltype(make_layout(Shape<_64, _32>{}, GenColMajor{}));
    using STile = decltype(make_layout(Shape<_32, _32>{}, GenColMajor{}));
    auto gA = make_managed_tensor<float>(GSlab{});
    auto gB = make_managed_tensor<float>(GSlab{});
    for (int i = 0; i < size(gA); i++) { gA(i) = i; }
    auto mosaic = MoveMosaic_sm80<float, 32, LayoutShape(GSlab), LayoutShape(STile), GSlab, GSlab>{};
    int blocks = size(mosaic.Blocks);
    tiled_move_kernel<<<blocks, int(mosaic.thread_num)>>>(mosaic, gA.data(), gB.data());
    cudaDeviceSynchronize();
    ASSERT_EQ(cudaGetLastError(), cudaSuccess);
    bool match = check_tensors_match(gA, gB, 0., false);
    ASSERT_TRUE(match);
}

template<typename T, int thread_num, typename SlabShape, typename TileShape, typename ASlab, typename BSlab>
void test_tile_move_mosaic() {
    auto gA = make_managed_tensor<T>(ASlab{});
    auto gB = make_managed_tensor<T>(BSlab{});
    for (int i = 0; i < size(gA); i++) { gA(i) = i; }
    auto mosaic = MoveMosaic_sm80<T, thread_num, SlabShape, TileShape, ASlab, BSlab>{};
    int blocks = size(mosaic.Blocks);
    tiled_move_kernel<<<blocks, thread_num>>>(mosaic, gA.data(), gB.data());
    cudaDeviceSynchronize();
    ASSERT_EQ(cudaGetLastError(), cudaSuccess);
    bool match = check_tensors_match(gA, gB, 0., false);
    ASSERT_TRUE(match);
}

// TODO: add tests where STile.shape != TileShape (it must be compatible though)
TEST(CopyMosaicTest, Copy) {
    {
        using M = Int<32>; using N = Int<32>;
        using ProblemShape = Shape<M, N>;
        using B = Layout<ProblemShape>;
        using A = Layout<ProblemShape>;
        using TileShape = Shape<_32, _32>;
        test_tile_move_mosaic<float, 32, ProblemShape, TileShape, A, B>();
    }
    {
        using M = Int<64>; using N = Int<32>;
        using ProblemShape = Shape<M, N>;
        using B = Layout<ProblemShape>;
        using A = Layout<ProblemShape, Stride<N, _1>>;
        using TileShape = Shape<_32, _32>;
        test_tile_move_mosaic<float, 32, ProblemShape, TileShape, A, B>();
    }
    {
        using M = Int<64>; using N = Int<32>;
        using ProblemShape = Shape<M, N>;
        using B = Layout<ProblemShape>;
        using A = Layout<ProblemShape, Stride<N, _1>>;
        using TileShape = Shape<_32, _32>;
        test_tile_move_mosaic<half_t, 64, ProblemShape, TileShape, A, B>();
    }
    { 
        using M = Int<64>; using N = Int<32>;
        using ProblemShape = Shape<M, N>;
        using B = Layout<ProblemShape, Stride<N, _1>>;
        using A = Layout<ProblemShape, Stride<N, _1>>;
        using TileShape = Shape<_32, _32>;
        test_tile_move_mosaic<half_t, 128, ProblemShape, TileShape, A, B>();
    }
} 

TEST(CopyMosaicTest, NestedCopy) {
    { 
        using M = Int<64>; using N = Int<32>; using K = Int<16>;
        using ProblemShape = Shape<Shape<M, N>, K>;
        using A = Layout<ProblemShape>;
        using B = Layout<ProblemShape>;
        using TileShape = Shape<Shape<_8, _8>, _2>;
        test_tile_move_mosaic<float, 32, ProblemShape, TileShape, A, B>();
    }
    { 
        using M = Int<64>; using N = Int<32>; using K = Int<16>;
        using ProblemShape = Shape<Shape<M, N>, K>;
        using A = Layout<ProblemShape, Stride<Stride<K,decltype(K{}*M{})>,_1>>;
        using B = Layout<ProblemShape, Stride<Stride<N,_1>,decltype(M{}*N{})>>;
        using TileShape = Shape<Shape<_4, _8>, _2>;
        test_tile_move_mosaic<float, 32, ProblemShape, TileShape, A, B>();
    }
}

} // namespace
} // namespace mosaic