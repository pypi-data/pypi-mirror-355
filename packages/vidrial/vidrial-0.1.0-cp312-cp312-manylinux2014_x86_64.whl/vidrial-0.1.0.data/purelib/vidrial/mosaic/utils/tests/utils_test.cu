#include <gtest/gtest.h>
#include "utilities.cuh"

namespace mosaic {
namespace {

TEST(BroadcastTest, BroadcastSet) {
    {
        const int I = 4; const int J = 5; const int match_dim=0;
        auto Xshape = make_shape(Int<I>{});
        auto Yshape = make_shape(Int<I>{}, Int<J>{});
        auto X = arange_tensor<int>(make_layout(Xshape));
        auto Y = make_tensor<int>(make_layout(Yshape));
        broadcast_set<match_dim>(X, Y);
        for (int i = 0; i < I; ++i) {
            for (int j = 0; j < J; ++j) {
                EXPECT_EQ(Y(i, j), X(i));
            }
        }
    }
    {
        const int I = 2; const int J = 3; const int match_dim=1;
        auto Xshape = make_shape(Int<J>{});
        auto Yshape = make_shape(Int<I>{}, Int<J>{});
        auto X = arange_tensor<int>(make_layout(Xshape));
        auto Y = make_tensor<int>(make_layout(Yshape));
        broadcast_set<match_dim>(X, Y);
        for (int i = 0; i < I; ++i) {
            for (int j = 0; j < J; ++j) {
                EXPECT_EQ(Y(i, j), X(j));
            }
        }
    }
}

TEST(BroadcastTest, BroadcastMultiply) {
    {
        const int I = 4; const int J = 5; const int match_dim=0;
        auto Xshape = make_shape(Int<I>{});
        auto Yshape = make_shape(Int<I>{}, Int<J>{});
        auto X = arange_tensor<int>(make_layout(Xshape));
        auto Y_ref = arange_tensor<int>(make_layout(Yshape));
        auto Y = arange_tensor<int>(make_layout(Yshape));
        broadcast_multiply<match_dim>(X, Y);
        for (int i = 0; i < I; ++i) {
            for (int j = 0; j < J; ++j) {
                EXPECT_EQ(Y(i, j), X(i)*Y_ref(i, j));
            }
        }
    }
    {
        const int I = 2; const int J = 3; const int match_dim=1;
        auto Xshape = make_shape(Int<J>{});
        auto Yshape = make_shape(Int<I>{}, Int<J>{});
        auto X = arange_tensor<int>(make_layout(Xshape));
        auto Y = arange_tensor<int>(make_layout(Yshape));
        auto Y_ref = arange_tensor<int>(make_layout(Yshape));
        broadcast_multiply<match_dim>(X, Y);
        for (int i = 0; i < I; ++i) {
            for (int j = 0; j < J; ++j) {
                EXPECT_EQ(Y(i, j), X(j)*Y_ref(i, j));
            }
        }
    }
}

TEST(ZipNestedTest, BasicZip) {
    auto s = tuple<tuple<int, int>, int>{};
    auto t0 = make_tuple(make_tuple(_1{}, _1{}), _1{});
    auto t1 = make_tuple(make_tuple(_2{}, _2{}), _2{});
    auto t2 = make_tuple(make_tuple(_3{}, _3{}), _3{});

    auto correct_unary = make_tuple(
        make_tuple(make_tuple(_1{}),
                  make_tuple(_1{})),
        make_tuple(_1{}));
    EXPECT_TRUE((zip_nested(s, t0) == correct_unary));
    EXPECT_TRUE((zip_nested_tuple(s, make_tuple(t0)) == correct_unary));


    auto correct_binary = make_tuple(
        make_tuple(make_tuple(_1{}, _2{}),
                  make_tuple(_1{}, _2{})),
        make_tuple(_1{}, _2{}));
    EXPECT_TRUE((zip_nested(s, t0, t1) == correct_binary));
    EXPECT_TRUE((zip_nested_tuple(s, make_tuple(t0, t1)) == correct_binary));

    auto correct_multi = make_tuple(
        make_tuple(make_tuple(_1{}, _2{}, _3{}),
                  make_tuple(_1{}, _2{}, _3{})),
        make_tuple(_1{}, _2{}, _3{}));
    EXPECT_TRUE((zip_nested(s, t0, t1, t2) == correct_multi));
    EXPECT_TRUE((zip_nested_tuple(s, make_tuple(t0, t1, t2)) == correct_multi));
}

TEST(GetMajorDimTest, BasicLayouts) {
    using namespace cute;
    {
        auto L = Layout<Shape<_2, _2, _2>>{};
        constexpr int major_dim = flat_major_dim(L);
        EXPECT_EQ(major_dim, 0);
    }
    {
        auto L = Layout<Shape<Int<32>,Int<16>>,Stride<Int<32>,Int<1>>>{};
        constexpr int major_dim = flat_major_dim(L);
        EXPECT_EQ(major_dim, 1);
    }
    {
        auto L = Layout<Shape<_32, _8, _2>, Stride<_2, _64, _1>>{};
        constexpr int major_dim = flat_major_dim(L);
        EXPECT_EQ(major_dim, 2);
    }
}

TEST(FactorTest, FactorOf12) {
    constexpr auto factors_12 = factor<12>();
    // Verify size
    EXPECT_EQ(rank(factors_12), 6);
    // Verify individual factors
    EXPECT_EQ(get<0>(factors_12).value, 1);
    EXPECT_EQ(get<1>(factors_12).value, 2);
    EXPECT_EQ(get<2>(factors_12).value, 3);
    EXPECT_EQ(get<3>(factors_12).value, 4);
    EXPECT_EQ(get<4>(factors_12).value, 6);
    EXPECT_EQ(get<5>(factors_12).value, 12);
}

TEST(FactorTest, FactorOf16) {
    constexpr auto factors_16 = factor<16>();
    // Verify size
    EXPECT_EQ(rank(factors_16), 5);
    // Verify individual factors
    EXPECT_EQ(get<0>(factors_16).value, 1);
    EXPECT_EQ(get<1>(factors_16).value, 2);
    EXPECT_EQ(get<2>(factors_16).value, 4);
    EXPECT_EQ(get<3>(factors_16).value, 8);
    EXPECT_EQ(get<4>(factors_16).value, 16);
}

TEST(FactorTest, PrimeFactorOf12) {
    // Test prime factors
    constexpr auto prime_fac_12 = prime_factors<12>();
    // Verify size
    EXPECT_EQ(rank(prime_fac_12), 3);
    // Verify prime factors (2 × 2 × 3)
    EXPECT_EQ(get<0>(prime_fac_12).value, 2);
    EXPECT_EQ(get<1>(prime_fac_12).value, 2);
    EXPECT_EQ(get<2>(prime_fac_12).value, 3);
}

TEST(FactorTest, PrimeFactorOf16) {
    // Test prime factors
    constexpr auto prime_fac_16 = prime_factors<16>();
    // Verify size
    EXPECT_EQ(rank(prime_fac_16), 4);
    // Verify prime factors (2 × 2 × 2 × 2)
    EXPECT_EQ(get<0>(prime_fac_16).value, 2);
    EXPECT_EQ(get<1>(prime_fac_16).value, 2);
    EXPECT_EQ(get<2>(prime_fac_16).value, 2);
    EXPECT_EQ(get<3>(prime_fac_16).value, 2);
}

TEST(FactorTest, PrimeFactorOf17) {
    constexpr auto prime_fac_17 = prime_factors<17>();
    // Verify size
    EXPECT_EQ(rank(prime_fac_17), 1);
    // Verify prime factors (17 is prime)
    EXPECT_EQ(get<0>(prime_fac_17).value, 17);
}

TEST(FactorTest, FactorPairsOf12) {
    // Test factor pairs
    constexpr auto factor_pairs_12 = factor_pairs<12>();
    // Verify size
    EXPECT_EQ(rank(factor_pairs_12), 3);
    
    // Verify factor pairs: (1,12), (2,6), (3,4)
    EXPECT_TRUE(find(factor_pairs_12, make_tuple(Int<1>{}, Int<12>{})) < 3);
    EXPECT_TRUE(find(factor_pairs_12, make_tuple(Int<2>{}, Int<6>{})) < 3);
    EXPECT_TRUE(find(factor_pairs_12, make_tuple(Int<3>{}, Int<4>{})) < 3);
}

TEST(FactorTest, FactorPairsOf16) {
    // Test with a perfect square - factor pairs should include the sqrt only once
    constexpr auto factor_pairs_16 = factor_pairs<16>();
    // Verify size
    EXPECT_EQ(rank(factor_pairs_16), 3);
    
    // Verify factor pairs: (1,16), (2,8), (4,4)
    EXPECT_TRUE(find(factor_pairs_16, make_tuple(Int<1>{}, Int<16>{})) < 3);
    EXPECT_TRUE(find(factor_pairs_16, make_tuple(Int<2>{}, Int<8>{})) < 3);
    EXPECT_TRUE(find(factor_pairs_16, make_tuple(Int<4>{}, Int<4>{})) < 3);
}

TEST(FactorTest, FactorPairsOf17) {
    // Test with a prime number - should only have (1,n) as factor pair
    constexpr auto factor_pairs_17 = factor_pairs<17>();
    // Verify size
    EXPECT_EQ(rank(factor_pairs_17), 1);
    
    // Verify factor pair: (1,17)
    EXPECT_TRUE(find(factor_pairs_17, make_tuple(Int<1>{}, Int<17>{})) < 1);
}

TEST(FactorTest, FactorPairsOf64) {
    // Demonstrate compile-time usage
    constexpr auto layout_factors = factor_pairs<64>();
    EXPECT_EQ(rank(layout_factors), 4);
    
    // Verify factor pairs: (1,64), (2,32), (4,16), (8,8)
    EXPECT_TRUE(find(layout_factors, make_tuple(Int<1>{}, Int<64>{})) < 4);
    EXPECT_TRUE(find(layout_factors, make_tuple(Int<2>{}, Int<32>{})) < 4);
    EXPECT_TRUE(find(layout_factors, make_tuple(Int<4>{}, Int<16>{})) < 4);
    EXPECT_TRUE(find(layout_factors, make_tuple(Int<8>{}, Int<8>{})) < 4);
}

TEST(FactorTest, FactorOf64) {
    // Demonstrate compile-time usage
    constexpr auto factors_64 = factor<64>();
    EXPECT_EQ(rank(factors_64), 7);
    
    // Verify factors: 1, 2, 4, 8, 16, 32, 64
    EXPECT_TRUE(find(factors_64, Int<1>{}) < 7);
    EXPECT_TRUE(find(factors_64, Int<2>{}) < 7);
    EXPECT_TRUE(find(factors_64, Int<4>{}) < 7);
    EXPECT_TRUE(find(factors_64, Int<8>{}) < 7);
    EXPECT_TRUE(find(factors_64, Int<16>{}) < 7);
    EXPECT_TRUE(find(factors_64, Int<32>{}) < 7);
    EXPECT_TRUE(find(factors_64, Int<64>{}) < 7);
}

TEST(LargestContiguousCosizeTest, BasicLayouts) {
    constexpr auto L = Layout<Shape<Shape<_2, _2, _2>, Shape<_4, _8>>,
                              Stride<Stride<_16, _8, _128>, Stride<_32, _1>>>{};
    constexpr auto contiguous_cosize = largest_contiguous_cosize(L);

    EXPECT_EQ(contiguous_cosize, 256);
}

TEST(LargestContiguousCosizeTest, NonContiguousLayout) {
    constexpr auto L = Layout<Shape<Shape<_2>, Shape<_4, _8>>,
                              Stride<Stride<_16>, Stride<_32, _1>>>{};
    constexpr auto contiguous_cosize = largest_contiguous_cosize(L);

    EXPECT_EQ(contiguous_cosize, 8);
}

TEST(LargestContiguousCosizeTest, NonContiguousLayout1) {
    constexpr auto L = Layout<Shape<Shape<_2>, Shape<_4>>,
                              Stride<Stride<_16>, Stride<_32>>>{};
    constexpr auto contiguous_cosize = largest_contiguous_cosize(L);

    EXPECT_EQ(contiguous_cosize, 1);
}

TEST(SizeDivideTest, BasicLayouts) {
    constexpr auto L = Layout<Shape<Shape<_2, _2, _2>, Shape<_4, _8>>,
                            Stride<Stride<_16, _8, _128>, Stride<_32, _1>>>{};
    constexpr auto divided = size_divide<16>(L);
    EXPECT_EQ(size<0>(divided), 16);
    EXPECT_EQ(size<1>(divided), 16);
}

} // namespace
} // namespace mosaic 