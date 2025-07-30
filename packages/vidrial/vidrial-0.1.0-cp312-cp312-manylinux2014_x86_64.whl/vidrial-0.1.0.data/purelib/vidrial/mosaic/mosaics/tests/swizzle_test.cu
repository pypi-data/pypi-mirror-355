#include <gtest/gtest.h>
#include <cuda_runtime.h>
#include "utilities.cuh"
#include "mma_mosaic.cuh"
#include "mma/kernel.cuh"
#include "sympow_mma_mosaic.cuh"
#include "swizzle_mosaic.cuh"
#include "ABC_utils.cuh"

using namespace cute;

namespace mosaic {
namespace {

TEST(SwizzleTest, case1) {
    using T = half_t;
    constexpr int power = 2;
    constexpr bool expand_K = false;
    constexpr int d_tile = 4;
    constexpr int d = 8;
    constexpr int D = sympow_dim<power, d, d_tile>();
    constexpr int M = D;
    constexpr int N = 256;
    constexpr int K = 256;
    constexpr int P = 13;
    constexpr int M_tile = static_pow<power>(d_tile);
    constexpr int N_tile = 16;
    constexpr int K_tile = 16;
    using MNKPSlabShape = Shape<Int<D>,Int<N>,Int<K>,Int<P>>; // M=256, N=256, K=256, P=13
    using MNKTileShape = Shape<Int<M_tile>,Int<N_tile>,Int<K_tile>>; // M_tile=64, N_tile=64, K_tile=16
    using GaSlab = Layout<Shape<Int<d>,Int<K>,Int<P>>>; // d, K, P
    using GBSlab = Layout<Shape<Int<N>,Int<K>,Int<P>>>; // N, K, P
    using GCSlab = Layout<Shape<Int<M>,Int<N>,Int<P>>>; // M, N, P
    using PerfMosaic = PerfMosaic<2, 1, true, 1>;
    using Atom = decltype(default_MMA_atom<T>());
    using MNKAtomPlacement = Shape<_1,_1,_1>;
    using SympowMMAMosaic_t = SympowMmaMosaic<T, power, Atom, MNKAtomPlacement, MNKPSlabShape, MNKTileShape, d, d_tile, expand_K, GaSlab, GBSlab, GCSlab, PerfMosaic>;
    SympowMMAMosaic_t mos;
    
    EXPECT_EQ((mos.A.swizzle_mos.swizzle), (Swizzle<Int<2>{}, Int<3>{}, Int<3>{}>{}));
    EXPECT_EQ((mos.B.swizzle_mos.swizzle), (Swizzle<Int<2>{}, Int<3>{}, Int<3>{}>{}));
}

TEST(SwizzleTest, case2) {
    using T = float;
    using Atom = decltype(default_MMA_atom<T>());
    using MNKAtomPlacement = Shape<_1,_1,_1>;
    using PerfMosaic = mosaic::PerfMosaic<2, 1, true, 1>;
    using Mosaic = mosaic::SympowMmaMosaic<float, 2, Atom, MNKAtomPlacement, cute::tuple<cute::C<48>, cute::C<64>, cute::C<64>, cute::C<1>>, cute::tuple<cute::C<16>, cute::C<16>, cute::C<16>>, 8, 4, false, cute::Layout<cute::tuple<cute::C<8>, cute::C<64>, cute::C<1>>, cute::tuple<cute::_1, cute::C<8>, cute::C<0>>>, cute::Layout<cute::tuple<cute::C<64>, cute::C<64>, cute::_1>, cute::tuple<cute::_1, cute::_64, cute::_0>>, cute::Layout<cute::tuple<cute::C<48>, cute::C<64>, cute::_1>, cute::tuple<cute::_1, cute::C<48>, cute::C<0>>>, PerfMosaic>;
    Mosaic mos;

    using namespace cute;
    // print("mos.A.mma_FrgThr: ");print(mos.A.mma_FrgThr);print("\n");
    // print("mos.A.sTile_: ");print(mos.A.sTile_);print("\n");
    // print("mos.A.sTile: ");print(mos.A.sTile);print("\n");
    // // print("mos.A.swizzle.read_atom: ");print(mos.A.swizzle.read_atom);print("\n");
    // print("mos.A.swizzle.frgThr: ");print(mos.A.swizzle.frgThr);print("\n");
    // print("mos.A.swizzle.srcFrgThr: ");print(mos.A.swizzle.srcFrgThr);print("\n");
    // print("mos.A.swizzle.srcfrg_major_mode: ");print(mos.A.swizzle.srcfrg_major_mode);print("\n");
    // print("mos.A.swizzle.srcfrg_contiguous_size: ");print(mos.A.swizzle.srcfrg_contiguous_size);print("\n");
    // print("mos.A.swizzle.M: ");print(mos.A.swizzle.M);print("\n");
    // print("mos.A.swizzle_mos.swizzle: ");print(mos.A.swizzle_mos.swizzle);print("\n");

    // print("mos.B.mma_FrgThr: ");print(mos.B.mma_FrgThr);print("\n");
    // print("mos.B.sTile_: ");print(mos.B.sTile_);print("\n");
    // auto is_B_ldsm_compatible = is_ldsm_compatible<T>(mos.B.sTile_, mos.B.mma_FrgThr);
    // print("is_B_ldsm_compatible: ");print(is_B_ldsm_compatible);print("\n");
    // print("mos.B.sTile: ");print(mos.B.sTile);print("\n");
    // // print("mos.B.swizzle.read_atom: ");print(mos.B.swizzle.read_atom);print("\n");
    // print("mos.B.swizzle.frgThr: ");print(mos.B.swizzle.frgThr);print("\n");
    // print("mos.B.swizzle.srcFrgThr: ");print(mos.B.swizzle.srcFrgThr);print("\n");
    // print("mos.B.swizzle.srcfrg_major_mode: ");print(mos.B.swizzle.srcfrg_major_mode);print("\n");
    // print("mos.B.swizzle.srcfrg_contiguous_size: ");print(mos.B.swizzle.srcfrg_contiguous_size);print("\n");
    // print("mos.B.swizzle.M: ");print(mos.B.swizzle.M);print("\n");
    // print("mos.B.swizzle_mos.swizzle: ");print(mos.B.swizzle_mos.swizzle);print("\n");

    EXPECT_EQ((mos.A.swizzle_mos.swizzle), (Swizzle<Int<3>{}, Int<2>{}, Int<3>{}>{}));
    EXPECT_EQ((mos.B.swizzle_mos.swizzle), (Swizzle<Int<3>{}, Int<2>{}, Int<3>{}>{}));
}


TEST(SwizzleTest, case3) {
    using G2SMosaic_ = mosaic::CopyMosaic_sm80<cutlass::bfloat16_t, 32, cute::tuple<cute::C<16L>, cute::C<16L>>, cute::Layout<cute::tuple<cute::C<16L>, cute::C<16L>>, cute::tuple<cute::C<1L>, cute::C<64L>>>, cute::Layout<cute::tuple<cute::C<16L>, cute::C<16L>>, cute::tuple<cute::C<1>, cute::C<16L>>>>;

    using STile_=cute::Layout<cute::tuple<cute::C<16L>, cute::C<16L>>, cute::tuple<cute::C<1>, cute::C<16L>>>;
    
    using FrgThr_=cute::Layout<cute::tuple<cute::tuple<cute::_2, cute::C<2L>, cute::C<2L>>, cute::tuple<cute::_4, cute::C<8>, cute::tuple<cute::_1, cute::_1, cute::_1>>>, cute::tuple<cute::tuple<cute::C<16L>, cute::C<8>, cute::C<128L>>, cute::tuple<cute::C<32L>, cute::_1, cute::tuple<cute::C<0>, cute::C<0>, cute::C<0>>>>>;    
    constexpr int swizzle_mode=0;

    using Mosaic = mosaic::SwizzleMosaic<G2SMosaic_, STile_, FrgThr_, swizzle_mode>;

    Mosaic mosaic;
    EXPECT_EQ((mosaic.swizzle), (Swizzle<Int<2>{}, Int<3>{}, Int<3>{}>{}));
    
}

TEST(SwizzleTest, case4) {
    using T = cutlass::half_t;
    using ABC_t = A_t;
    using MmaAtom = cute::MMA_Atom<cute::SM80_16x8x8_F32F16F16F32_TN>;
    using MNKTileShape = cute::tuple<cute::_16, cute::_16, cute::_16>;
    using MNKAtomPlacement = cute::tuple<cute::_1, cute::_2, cute::C<1>>;
    using GSlab = cute::Layout<cute::tuple<cute::_16, cute::_16, cute::_1>, cute::tuple<cute::_1, cute::_16, cute::C<0>>>;
    using PerfMosaic = mosaic::PerfMosaic<2, 1, true, 1>;
    using Mosaic = mosaic::ABC_Mosaic_sm80<T, ABC_t, MmaAtom, MNKTileShape, MNKAtomPlacement, GSlab, PerfMosaic>;
    Mosaic mos;

    EXPECT_EQ((mos.swizzle_mos.swizzle), (Swizzle<Int<2>{}, Int<3>{}, Int<3>{}>{}));
}

}
}// namespace mosaic