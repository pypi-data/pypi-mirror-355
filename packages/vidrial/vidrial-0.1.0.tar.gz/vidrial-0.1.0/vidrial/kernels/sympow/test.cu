#pragma once
#include <gtest/gtest.h>
#include "sympow.cuh"
#include "sympow_mosaic.cuh"
#include "kernel.cuh"
#include <type_traits>  // For std::remove_reference

namespace mosaic {
namespace {

/* The following 3 tests check for the following fundamental properties of sympow
- When d=d_tile, sympow is equivalent to tpow
- When duplicate_corrections=true, sympow expansion preserves the innerproducts of tpow expansion
- When duplicate_corrections=false, sympow produces tensors with hypercube tiles matching those of tpow
*/
template<typename T, int p, int d, int b>
void test_sympow_tpow_match() {
    auto XShape = Shape<Int<d>, Int<b>>{};
    auto ZShape = sympow_shape<p, d, b, d>();
    auto YShape = tpow_shape<p>(XShape);
    auto gX = make_managed_tensor<T>(make_layout(XShape));
    auto gZ = make_managed_tensor<T>(make_layout(ZShape));
    auto gY = make_managed_tensor<T>(make_layout(YShape));
    for (int i = 0; i < size(gX); ++i) gX(i) = static_cast<T>(i);
    sympow<p, d>(gZ, gX);
    tpow<p>(gY, gX);
    bool match = check_tensors_match(gZ, gY, 0., false);
    ASSERT_TRUE(match);
}
template<typename T, int p, int d, int b, int d_tile>
void test_sympow_inner_product_match() {
    auto Shp = Shape<Int<d>, Int<b>>{};
    auto gA = make_managed_tensor<T>(make_layout(Shp));
    auto gB = make_managed_tensor<T>(make_layout(Shp));
    for (int i = 0; i < size(gA); ++i) gA(i) = static_cast<T>(i%27)/27;
    for (int i = 0; i < size(gB); ++i) gB(i) = static_cast<T>(i%14)/14;
    // Compute the tensor power of gA and gB, take the inner products
    auto pow_Shp = tpow_shape<p>(Shp);
    auto gA_pow = make_managed_tensor<T>(make_layout(pow_Shp));
    auto gB_pow = make_managed_tensor<T>(make_layout(pow_Shp));
    tpow<p>(gA_pow, gA);
    tpow<p>(gB_pow, gB);
    auto y_ref = make_managed_tensor<float>(make_layout(Int<b>{}));
    tensor_inner_prods(y_ref, gA_pow, gB_pow);
    // We should get the same inner products when expanding with sympow
    constexpr auto sympow_dims = NonDecSeq<int(d/d_tile), 2>{}.num_elements * d_tile * d_tile;
    auto sympow_Shp = sympow_shape<p, d, b, d_tile>();
    auto gA_sympow = make_managed_tensor<T>(make_layout(sympow_Shp));
    auto gB_sympow = make_managed_tensor<T>(make_layout(sympow_Shp));
    sympow<p, d_tile, true>(gA_sympow, gA); // duplicate_correction=true because we want the inner product to match
    sympow<p, d_tile, true>(gB_sympow, gB);
    auto y = make_managed_tensor<float>(make_layout(Int<b>{}));
    tensor_inner_prods(y, gA_sympow, gB_sympow);
    bool match = check_tensors_match(y, y_ref, 1e-3, false);
    EXPECT_TRUE(match);
}
// Test the fundamental relationship between the entries of tprods and sympows
template<int p, int d, int b, int d_tile>
void test_tprod_sympow_matching_entires() {
    using T = float;
    auto XShape = Shape<Int<d>, Int<b>>{};
    auto YShape = tpow_shape<p>(XShape);
    auto ZShape = sympow_shape<p, d, b, d_tile>();
    auto gX = make_managed_tensor<T>(make_layout(XShape));
    auto gY = make_managed_tensor<T>(make_layout(YShape));
    auto gZ = make_managed_tensor<T>(make_layout(ZShape));
    for (int i = 0; i < size(gX); ++i) gX(i) = static_cast<T>(i%27)/27;
    tpow<p>(gY, gX);
    sympow<p, d_tile, false>(gZ, gX); // duplicate_correction=false because we want the entries with the tprod to match
    auto TileShape = tpow_shape<p>(Shape<Int<d_tile>,Int<b>>{});
    auto gY_TileBlock = zipped_divide(gY, TileShape);
    using Coords = NonDecSeq<d/d_tile, p>;
    for (Coords c{}; c.idx < c.num_elements; ++c) {
        auto tprod_block = make_coord(c.seq, _0{});
        auto gY_tile = slice_rest(gY_TileBlock, tprod_block);
        auto gZ_tile = gZ(make_coord(_,c.idx),_);
        bool match = check_tensors_match(gY_tile, gZ_tile, 0., false);
        EXPECT_TRUE(match);
    }
}

// with a block size of 1
TEST(Sympow, ManualSympowMatch) {
    using T = float;
    auto d = Int<8>{};
    auto b = Int<4>{};
    auto d_tile = Int<1>{};
    auto XShape = Shape<decltype(d), decltype(b)>{};
    auto ZShape = sympow_shape<2, d, b, d_tile>();
    auto gX = make_managed_tensor<T>(make_layout(XShape));
    auto gZ = make_managed_tensor<T>(make_layout(ZShape));
    for (int i = 0; i < size(gX); ++i) gX(i) = static_cast<T>(i);
    sympow<2, d_tile>(gZ, gX);
    auto gZ_ref = make_managed_tensor<T>(make_layout(ZShape));
    for (int k=0; k<b; ++k) {
        int idx = 0;
        for (int i=0; i<d; ++i) {
            for (int j=i; j<d; ++j) {
                gZ_ref(idx,k) = gX(i,k) * gX(j,k);
                idx++;
            }
        }
    }
    bool match = check_tensors_match(gZ, gZ_ref, 0., false);
    ASSERT_TRUE(match);
}

TEST(Sympow, TprodMatch) {
    test_sympow_tpow_match<float, 2, 4, 1>();
    test_sympow_tpow_match<float, 2, 64, 4>();
    test_sympow_tpow_match<float, 3, 64, 1>();
    test_sympow_tpow_match<float, 4, 16, 1>();
    test_sympow_tpow_match<float, 4, 32, 1>();
}

TEST(Sympow, InnerProduct) {
                                //     <T, p, d, b, d_tile>
    test_sympow_inner_product_match<float, 2, 4, 1, 1>();
    test_sympow_inner_product_match<float, 2, 64, 4, 8>();
    test_sympow_inner_product_match<float, 3, 64, 1, 8>();
    test_sympow_inner_product_match<float, 4, 32, 1, 8>();
}

TEST(Sympow, MatchingEntriesWithTprod) {
                                   // <p, d, b, d_tile>
    test_tprod_sympow_matching_entires<2, 4, 4, 1>();
    test_tprod_sympow_matching_entires<2, 4, 4, 2>();
    test_tprod_sympow_matching_entires<2, 16, 2, 4>();
    test_tprod_sympow_matching_entires<3, 3, 1, 1>();
    test_tprod_sympow_matching_entires<3, 16, 2, 4>();
    test_tprod_sympow_matching_entires<4, 2, 1, 1>();
    test_tprod_sympow_matching_entires<4, 16, 2, 4>();
}

void test_NonDecSeq(auto c, auto& seqs_ref, auto& duplicate_counts_ref) {
   for (int i = 0; i < c.num_elements; ++i) {
      EXPECT_EQ(seqs_ref[i], c.seq);
      EXPECT_EQ(i, c.idx);
      EXPECT_EQ(duplicate_counts_ref[i], c.duplicate_count());
      ++c;
   }
}
template<typename SeqType, typename Seq, typename Dup>
__global__ void test_NonDecSeq_kernel(SeqType, Seq* seq_refs, Dup* duplicate_count_refs, bool* has_error) {
    SeqType c{};
    *has_error = true; // initialize assuming there is an error in case the kernel crashes and exits early
    bool any_error = false;
    for (int i = 0; i < c.num_elements; ++i) {
        if (i != c.idx || seq_refs[i] != c.seq || duplicate_count_refs[i] != c.duplicate_count()) {
            any_error = true;
        }
        ++c;
    }
    *has_error = any_error;
}
template<typename SeqType, typename Seq, typename Dup>
void test_NonDecSeq_gpu(SeqType c, Seq* seq_refs, Dup* duplicate_count_refs) {
    size_t seq_size = c.num_elements * sizeof(Seq);
    size_t dup_size = c.num_elements * sizeof(Dup);
    bool* d_has_error;
    Seq* d_seq_refs;
    Dup* d_dup_refs;
    cudaMallocManaged(&d_has_error, sizeof(bool));
    cudaMallocManaged(&d_seq_refs, seq_size);
    cudaMallocManaged(&d_dup_refs, dup_size);
    memcpy(d_seq_refs, seq_refs, seq_size);
    memcpy(d_dup_refs, duplicate_count_refs, dup_size);
    test_NonDecSeq_kernel<<<1,1>>>(c, d_seq_refs, d_dup_refs, d_has_error);
    CHECK_CUDA();
    EXPECT_FALSE(*d_has_error);
}

TEST(NonDecSeq, Rng2Len2) {
    tuple<int,int> arr[3] = {make_tuple(0,0),
                             make_tuple(0,1),
                             make_tuple(1,1)};
    int duplicate_counts[3] = {1, 2, 1};
    test_NonDecSeq( NonDecSeq<2, 2>{}, arr, duplicate_counts);
    test_NonDecSeq_gpu( NonDecSeq<2, 2>{}, arr, duplicate_counts);
}

TEST(NonDecSeq, Rng4Len2) {
    tuple<int,int> arr[10] = {make_tuple(0,0),
                             make_tuple(0,1),
                             make_tuple(0,2),
                             make_tuple(0,3),
                             make_tuple(1,1),
                             make_tuple(1,2),
                             make_tuple(1,3),
                             make_tuple(2,2),
                             make_tuple(2,3),
                             make_tuple(3,3)};
    int dupliate_counts[10] = {1,2,2,2,1,2,2,1,2,1};
    test_NonDecSeq( NonDecSeq<4, 2>{}, arr, dupliate_counts);
    test_NonDecSeq_gpu( NonDecSeq<4, 2>{}, arr, dupliate_counts);
}

TEST(NonDecSeqTest, Rng3Len3) {
    tuple<int,int,int> arr[10]={make_tuple(0,0,0), // 1
                                make_tuple(0,0,1), // 3
                                make_tuple(0,0,2), // 3
                                make_tuple(0,1,1), // 3
                                make_tuple(0,1,2), // 6
                                make_tuple(0,2,2), // 3
                                make_tuple(1,1,1), // 1
                                make_tuple(1,1,2), // 3
                                make_tuple(1,2,2), // 3
                                make_tuple(2,2,2)}; // 1
    int duplicate_counts[10] = {1,3,3,3,6,3,1,3,3,1};
   test_NonDecSeq( NonDecSeq<3, 3>{}, arr, duplicate_counts);
   test_NonDecSeq_gpu( NonDecSeq<3, 3>{}, arr, duplicate_counts);
}

TEST(NonDecSeqTest, Rng3Len4) {
    tuple<int,int,int,int> arr[15]={make_tuple(0,0,0,0), // 1
                                make_tuple(0,0,0,1), // 4
                                make_tuple(0,0,0,2), // 4
                                make_tuple(0,0,1,1), // 6
                                make_tuple(0,0,1,2), // 12
                                make_tuple(0,0,2,2), // 6
                                make_tuple(0,1,1,1), // 4
                                make_tuple(0,1,1,2), // 12
                                make_tuple(0,1,2,2), // 12
                                make_tuple(0,2,2,2), // 4
                                make_tuple(1,1,1,1), // 1
                                make_tuple(1,1,1,2), // 4
                                make_tuple(1,1,2,2), // 6
                                make_tuple(1,2,2,2), // 4
                                make_tuple(2,2,2,2)}; // 1
   int duplicate_counts[15] = {1, 4, 4, 6, 12, 6, 4, 12, 12, 4, 1, 4, 6, 4, 1};
   test_NonDecSeq( NonDecSeq<3, 4>{}, arr, duplicate_counts);
   test_NonDecSeq_gpu( NonDecSeq<3, 4>{}, arr, duplicate_counts);
}

} // namespace mosaic
} // namespace