#include <gtest/gtest.h>
#include "ABC_utils.cuh"
#include <iostream>
#include "sympow.cuh"
#include "sympow_mma_mosaic.cuh"
#include "kernels/sympow_mma/kernel.cuh"
#include "kernels/mma/kernel.cuh"
#include "kernels/sympow/kernel.cuh"

namespace mosaic {
namespace {


TEST(SympowMmaMosaic, RunExpandM) {
    constexpr bool expand_K = false;
    constexpr int d = 64;
    constexpr int d_tile = 8;
    constexpr int power = 2;
    constexpr int D = sympow_dim<power,d,d_tile>(); // 48
    constexpr int M = D, N = 64, K = 1024, P = 8;
    constexpr int N_TILE = 64;
    constexpr int K_TILE = 32;
    using MNKPSlabShape = Shape<Int<D>,Int<N>,Int<K>,Int<P>>;
    using MNKTileShape = Shape<Int<static_pow<power>(d_tile)>,Int<N_TILE>,Int<K_TILE>>;
    using GaSlab = Layout<Shape<Int<d>,Int<K>,Int<P>>, Stride<Int<K>, _1, Int<d * K>>>;
    using GBSlab = Layout<decltype(ABC_get_MNKP(B_t{}, MNKPSlabShape{})), Stride<_1, Int<d>, Int<d * K>>>;
    using GCSlab = Layout<decltype(ABC_get_MNKP(C_t{}, MNKPSlabShape{})), Stride<Int<d>, _1, Int<D * d>>>;
    // Test Input Data
    auto ga = make_managed_tensor<float>(GaSlab{});
    auto gB = make_managed_tensor<float>(GBSlab{});
    CHECK_CUDA(); // check the allocations didn't fail
    using Atom = decltype(default_MMA_atom<float>());
    using MNKAtomPlacement = Shape<_1,_1,_1>;
    using Mosaic = SympowMmaMosaic<float, power, Atom, MNKAtomPlacement, MNKPSlabShape, MNKTileShape, d, d_tile, expand_K, GaSlab, GBSlab, GCSlab>;
    auto gC = make_managed_tensor<float>(GCSlab{});
    launch_sympow_mma_kernel<true, 1>(Mosaic{}, ga.data(), gB.data(), gC.data());
    CHECK_CUDA();
}


/* This test compares a few different implementations of the same mathematical operation.
1. uses one of the 2 fused sympow_mma kernels using the SympowMmaMosaic
2. calls the sympow_kernel and then the mma_kernel using the 2 submosaics of SympowMmaMosaic
3. calls the sympow_kernel and then the mma_kernel using freshly constructed mosaics for each
4. single threaded cpu reference
*/
template<typename T, int pow, bool expand_K,
        int MorK, int N, int P,
        int MorK_tile, int N_tile, int d, int d_tile,
        bool duplicate_correction = false>
void test_sympow_mma_mosaic() {
    float tol = is_same_v<T, half_t> ? 1e-1 : 1e-3;
    tol += 1e-3 * pow; // we loose a bit of precision for large powers
    constexpr int D = sympow_dim<pow,d,d_tile>();
    constexpr int D_tile = static_pow<pow>(d_tile);
    constexpr int d_tile_num = sympow_dim<pow,d/d_tile>();
    constexpr int M = expand_K ? MorK : D;
    constexpr int K = expand_K ? D : MorK;
    constexpr int M_tile = expand_K ? MorK_tile : D_tile;
    constexpr int K_tile = expand_K ? D_tile : MorK_tile;
    using MNKPSlabShape = Shape<Int<M>,Int<N>,Int<K>,Int<P>>;
    using MNKTileShape = Shape<Int<M_tile>,Int<N_tile>,Int<K_tile>>;
    using XSlabShape = Shape<Int<d>,Shape<Int<MorK>,Int<P>>>;
    using ZSlabShape = decltype(sympow_shape<pow,d_tile>(XSlabShape{}));
    using GaSlab = conditional_t<expand_K,
                                Layout<Shape<Int<M>,Int<d>,Int<P>>>,
                                Layout<Shape<Int<d>,Int<K>,Int<P>>>>;
    using GBSlab = Layout<decltype(ABC_get_MNKP(B_t{}, MNKPSlabShape{}))>;
    using GCSlab = Layout<decltype(ABC_get_MNKP(C_t{}, MNKPSlabShape{}))>;
    // Test Input Data
    auto ga = make_managed_tensor<T>(GaSlab{});
    auto gB = make_managed_tensor<T>(GBSlab{});
    for (int i = 0; i < size(ga); ++i) ga(i) = static_cast<T>(i%14/14.);
    for (int i = 0; i < size(gB); ++i) gB(i) = static_cast<T>(i%27/27.);
    CHECK_CUDA(); // check the allocations didn't fail
    using Atom = decltype(default_MMA_atom<T>());
    using MNKAtomPlacement = Shape<_1,_1,_1>;
    // Fused Kernel
    using Mosaic = SympowMmaMosaic<T, pow, Atom, MNKAtomPlacement, MNKPSlabShape, MNKTileShape, d, d_tile, expand_K, GaSlab, GBSlab, GCSlab>;
    Mosaic mos{};
    auto gC = make_managed_tensor<T>(GCSlab{});
    launch_sympow_mma_kernel<duplicate_correction>(mos, ga.data(), gB.data(), gC.data());
    CHECK_CUDA();
    // GPU reference using mos.sympow and mos.mma
    auto gZ_ref1 = make_managed_tensor<T>(typename Mosaic::GZSlab{});
    auto gC_ref1 = make_managed_tensor<T>(GCSlab{});
    launch_tiled_sympow_kernel<duplicate_correction>(mos.sympow, gZ_ref1.data(), ga.data());
    launch_tiled_mma_kernel(mos.mma, gZ_ref1.data(), gB.data(), gC_ref1.data());
    CHECK_CUDA();
    EXPECT_TRUE(check_tensors_match(gC, gC_ref1, tol, false));
    // GPU reference using manually constructed sympow_mos and mma_mos
    using GZSlab_ref2 = Layout<ZSlabShape>;
    using GXSlab_ref2 = decltype(GaSlab{}.compose(typename Mosaic::X2aSlab{})); // converts the a layout to X layout depending on expand_K
    using GASlab_ref2 = decltype(GZSlab_ref2{}.compose(typename Mosaic::A2ZSlab{})); // converts the Z layout to A layout depending on expand_K
    auto gZ_ref2 = make_managed_tensor<T>(GZSlab_ref2{});
    auto gA_ref2 = make_tensor(gZ_ref2.data(), GASlab_ref2{}); // a view on the same data as gZ_ref2
    auto gC_ref2 = make_managed_tensor<T>(GCSlab{});
    using FrgShape = Shape<decltype(repeat<pow>(_2{})),_1>;
    auto sympow_mos = make_sympow_mosaic<T,pow>(FrgShape{}, typename Mosaic::XTileShape{}, GZSlab_ref2{}, GXSlab_ref2{}, Layout<typename Mosaic::ZTileShape>{});
    auto mma_mos = make_mma_mosaic<T>(MNKTileShape{}, gA_ref2.layout(), gB.layout(), gC_ref2.layout());
    launch_tiled_sympow_kernel<duplicate_correction>(sympow_mos, gZ_ref2.data(), ga.data());
    CHECK_CUDA();
    launch_tiled_mma_kernel(mma_mos, gZ_ref2.data(), gB.data(), gC_ref2.data());
    CHECK_CUDA();
    EXPECT_TRUE(check_tensors_match(gC, gC_ref2, tol, false));
    // CPU reference (reusing all the layouts from ref2)
    if (M <= 1024 && N <= 1024 && K <= 1024) { // skip for large sizes. Too slow.
        auto gC_ref3 = make_managed_tensor<T>(GCSlab{});
        auto gX_ref3 = make_tensor(ga.data(), GXSlab_ref2{});
        sympow<pow,d_tile,duplicate_correction>(gZ_ref2,gX_ref3);
        for (int p=0; p<P; p++) {
            gemm(gA_ref2(_,_,p),gB(_,_,p),gC_ref3(_,_,p));
        }
        EXPECT_TRUE(check_tensors_match(gC, gC_ref3, tol, false));
    }
}

/* Running the complete set of tests took 538 seconds. Most of the time is spent
on the cpu check_tensors_match. Without it it just takes 111 seconds.
TODO: write a gpu version of check_tensors_match. */
TEST(SympowMmaMosaic, float_pow2_expand_M_M64_N64_P1_Ktile16_Ntile16_d8_dtile4) {
    test_sympow_mma_mosaic<float, 2, false, 64, 64, 1, 16, 16, 8, 4>();
}
TEST(SympowMmaMosaic, float_pow3_expand_M_M64_N64_P1_Ktile16_Ntile16_d8_dtile4) {
    test_sympow_mma_mosaic<float, 3, false, 64, 64, 1, 16, 16, 8, 4>();
}
TEST(SympowMmaMosaic, float_pow4_expand_M_M64_N64_P1_Ktile16_Ntile16_d8_dtile4) {
    test_sympow_mma_mosaic<float, 4, false, 64, 64, 1, 16, 16, 8, 4>();
}
TEST(SympowMmaMosaic, float_pow2_expand_K_M64_N64_P1_Mtile16_Ntile16_d8_dtile4) {
    test_sympow_mma_mosaic<float, 2, true, 64, 64, 1, 16, 16, 8, 4>();
}
TEST(SympowMmaMosaic, float_pow3_expand_K_M64_N64_P1_Ktile16_Ntile16_d8_dtile4) {
    test_sympow_mma_mosaic<float, 3, true, 64, 64, 1, 16, 16, 8, 4>();
}
TEST(SympowMmaMosaic, float_pow4_expand_K_M64_N64_P1_Ktile16_Ntile16_d8_dtile4) {
    test_sympow_mma_mosaic<float, 4, true, 64, 64, 1, 16, 16, 8, 4>();
}
TEST(SympowMmaMosaic, float_pow2_expand_K_M16_N16_P1_Mtile16_Ntile16_d8_dtile4) {
    test_sympow_mma_mosaic<float, 2, true, 16, 16, 1, 16, 16, 8, 4>();
}
TEST(SympowMmaMosaic, half_pow2_expand_K_M16_N16_P1_Mtile16_Ntile16_d8_dtile8) {
    test_sympow_mma_mosaic<half_t, 2, true, 16, 16, 1, 16, 16, 8, 8>();
}
TEST(SympowMmaMosaic, half_pow3_expand_K_M64_N64_P1_Mtile16_Ntile16_d8_dtile4) {
    test_sympow_mma_mosaic<half_t, 3, true, 64, 64, 1, 16, 16, 8, 4>();
}


// TEST(SympowMmaMosaic, float_expand_K_M64_N64_P1_Mtile16_Ntile16_d8_dtile8) {
//     test_sympow_mma_mosaic<float, true, 64, 64, 1, 16, 16, 8, 8>();
// }
// TEST(SympowMmaMosaic, half_expand_M_M2048_N2048_P8_Mtile64_Ntile64_d64_dtile4) {
//     test_sympow_mma_mosaic<half_t, false, 2048, 2048, 8, 64, 64, 64, 4>();
// }
// TEST(SympowMmaMosaic, half_expand_M_M2048_N2048_P8_Mtile64_Ntile64_d64_dtile8) {
//     test_sympow_mma_mosaic<half_t, false, 2048, 2048, 8, 64, 64, 64, 8>();
// }
// TEST(SympowMmaMosaic, half_expand_K_M2048_N2048_P8_Mtile64_Ntile64_d64_dtile4) {
//     test_sympow_mma_mosaic<half_t, true, 2048, 2048, 8, 64, 64, 64, 4>();
// }
// TEST(SympowMmaMosaic, half_expand_K_M2048_N2048_P8_Mtile64_Ntile64_d64_dtile8) {
//     test_sympow_mma_mosaic<half_t, true, 2048, 2048, 8, 64, 64, 64, 8>();
// }
// TEST(SympowMmaMosaic, half_expand_M_M4096_N4096_P8_Mtile64_Ntile64_d64_dtile8) {
//     test_sympow_mma_mosaic<half_t, false, 4096, 4096, 8, 64, 64, 64, 8>();
// }
// TEST(SympowMmaMosaic, half_expand_K_M4096_N4096_P8_Mtile64_Ntile64_d64_dtile8) {
//     test_sympow_mma_mosaic<half_t, true, 4096, 4096, 8, 64, 64, 64, 8>();
// }
// TEST(SympowMmaMosaic, half_expand_K_M4096_N64_P8_Mtile64_Ntile64_d64_dtile8) {
//     test_sympow_mma_mosaic<half_t, true, 4096, 64, 8, 64, 64, 64, 8>();
// }
// TEST(SympowMmaMosaic, half_expand_K_M4096_N4096_P64_Mtile64_Ntile64_d64_dtile8) {
//     // This test is infamous example where the static integer overflow issue was encounterd.
//     // If the necessary global layouts are Int64 it should pass
//     test_sympow_mma_mosaic<half_t, true, 4096, 4096, 64, 64, 64, 64, 8>();
// }
// TEST(SympowMmaMosaic, half_expand_M_M4096_N4096_P64_Mtile64_Ntile64_d64_dtile8) {
//     test_sympow_mma_mosaic<half_t, false, 4096, 4096, 64, 64, 64, 64, 8>();
// }

}
}