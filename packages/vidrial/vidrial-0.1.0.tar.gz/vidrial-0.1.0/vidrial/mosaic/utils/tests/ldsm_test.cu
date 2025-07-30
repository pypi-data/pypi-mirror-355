#include <gtest/gtest.h>
#include <cuda_runtime.h>
#include "utilities.cuh"
#include "mma_mosaic.cuh"
#include "mma/kernel.cuh"
#include "ABC_utils.cuh"

using namespace cute;

namespace mosaic {
namespace {

template<typename Mosaic>
void debug_print(Mosaic mos) {
    print("====A====\n");
    print("mos.A.mma_FrgThr: ");print(mos.A.mma_FrgThr);print("\n");
    print("mos.A.mma_Frg: ");print(mos.A.mma_Frg);print("\n");
    print("mos.A.AtomShape: ");print(mos.A.AtomShape);print("\n");
    print("mos.A.mma_Atom: ");print(mos.A.mma_Atom);print("\n");
    print("mos.A.sTile: ");print(mos.A.sTile);print("\n");
    print("\n====B====\n");
    print("mos.B.mma_FrgThr: ");print(mos.B.mma_FrgThr);print("\n");
    print("mos.B.mma_Frg: ");print(mos.B.mma_Frg);print("\n");
    print("mos.B.AtomShape: ");print(mos.B.AtomShape);print("\n");
    print("mos.B.mma_Atom: ");print(mos.B.mma_Atom);print("\n");
    print("mos.B.sTile: ");print(mos.B.sTile);print("\n");
    
    print("\n====C====\n");
    print("mos.C.mma_FrgThr: ");print(mos.C.mma_FrgThr);print("\n");
    print("mos.C.mma_Frg: ");print(mos.C.mma_Frg);print("\n");
    print("mos.C.AtomShape: ");print(mos.C.AtomShape);print("\n");
    print("mos.C.mma_Atom: ");print(mos.C.mma_Atom);print("\n");
    print("mos.C.sTile: ");print(mos.C.sTile);print("\n");
}

template<typename CopyAtom, typename FrgThr, typename STile>
constexpr bool is_copy_atom_compatible_debug(CopyAtom atom, STile sTile, FrgThr frgThr) {
    using T = typename CopyAtom::ValType;
    using Frg = decltype(get<0>(FrgThr{}));

    print("frgThr: ");print(frgThr);print("\n");
    auto src_frg = slice_src_frg(sTile, atom, frgThr, Int<0>{});
    // using DstFrg = decltype(retile_dst_frg(atom, frgThr, Frg{}));
    auto dst_frg = retile_dst_frg(atom, frgThr, make_layout(Frg{}.shape()));

    if (size(Frg{}) != size(dst_frg))
        return false;
    print("src_frg: ");print(src_frg);print("\n");
    print("dst_frg: ");print(dst_frg);print("\n");

    // Step 1: check if the src_frg and dst_frg are compatible with each other
    // * check if they have the same size of rest modes
    if (rank(src_frg) != rank(dst_frg))
        return false;
    constexpr int R = rank(src_frg);
    auto src_v = group<1,R>(src_frg);
    auto dst_v = group<1,R>(dst_frg);
    print("src_v: ");print(src_v);print("\n");
    print("dst_v: ");print(dst_v);print("\n");
    if (size<1>(src_v) != size<1>(dst_v))
        return false;
    auto dst_null = decltype(nullspace(layout<1>(decltype(dst_frg){}))){};
    auto dst_n = decltype(zipped_divide(dst_v, make_tile(shape<0>(dst_v), dst_null))){};
    auto src_n = decltype(zipped_divide(src_v, make_tile(shape<0>(src_v), dst_null))){};
    if (size<1>(dst_n) != size<1>(src_n))
        return false;
    if (decltype(cosize<0,1>(dst_n) != Int<1>{})::value)
        return false;
    if (decltype(cosize<0,1>(src_n) != Int<1>{})::value)
        return false;
    if (decltype(size<1,0>(dst_n) != Int<1>{})::value)
        return false;
    if (decltype(size<1,0>(src_n) != Int<1>{})::value)
        return false;
     auto dst_c = dst_n(make_coord(_, Int<0>{}),make_coord(Int<0>{},_));
     auto src_c = src_n(make_coord(_, Int<0>{}),make_coord(Int<0>{},_));
    if (decltype(size<1>(dst_c) != size<1>(src_c))::value)
        return false;
    if (decltype(shape<0>(dst_c) != shape<0>(dst_frg))::value)
        return false;
    if (decltype(shape<0>(src_c) != shape<0>(src_frg))::value)
        return false;

    // Step 2: check if the src_frg and dst_frg are compatible with the copy atom
    using Traits = typename CopyAtom::Traits;
    using CopyOp = typename CPY_Op<Traits>::type;
    using RegistersSrc = typename CopyOp::SRegisters;
    using RegistersDst = typename CopyOp::DRegisters;
    using RegTypeSrc   = typename remove_extent<RegistersSrc>::type;
    using RegTypeDst   = typename remove_extent<RegistersDst>::type;
    using SRC_V = decltype(get<0>(src_v));
    using DST_V = decltype(get<0>(dst_v));
    constexpr int RegNumSrc = extent<RegistersSrc>::value;
    constexpr int RegNumDst = extent<RegistersDst>::value;

    constexpr auto rS = recast_layout<T, RegTypeSrc>(SRC_V{});
    constexpr auto rD = recast_layout<T, RegTypeDst>(DST_V{});
    if ((size(rS) != cosize(rS)) || (size(rD) != cosize(rD)))
        return false;
    if (size(rS) != Int<RegNumSrc>{})
        return false;
    if (size(rD) != Int<RegNumDst>{})
        return false;
        
    return true;
}

// Base case : 16x8x8 tile, column major, we should find transposed 16x4 atom for A and 16x2 for B
TEST(LDSMTest, tile_16_8_8_U16x4_T) {
    using T = half_t;
    using MNKPSlabShape = Shape<_64, _64, _64, _4>;
    using MNKTileShape = Shape<_16,_8,_8>;
    using ASlab = Layout<decltype(ABC_get_MNKP(A_t{}, MNKPSlabShape{}))>;
    using BSlab = Layout<decltype(ABC_get_MNKP(B_t{}, MNKPSlabShape{}))>;
    using CSlab = Layout<decltype(ABC_get_MNKP(C_t{}, MNKPSlabShape{}))>;

    auto mos = mosaic::make_mma_mosaic<T>(MNKTileShape{}, ASlab{}, BSlab{}, CSlab{});


    auto is_A_compatible = is_copy_atom_compatible(Copy_Atom<SM75_U16x4_LDSM_T, T>{}, mos.A.unswizzled_sTile, mos.A.mma_FrgThr);
    auto is_B_compatible = is_copy_atom_compatible(Copy_Atom<SM75_U16x4_LDSM_T, T>{}, mos.B.unswizzled_sTile, mos.B.mma_FrgThr);
    // EXPECT_TRUE(is_A_compatible) << "LDSM atom A should be compatible";
    EXPECT_FALSE(is_B_compatible) << "LDSM atom B should not be compatible";
    auto ldsm_atom_A = compatible_ldsm_atom<T>(mos.A.unswizzled_sTile, mos.A.mma_FrgThr);
    auto ldsm_atom_B = compatible_ldsm_atom<T>(mos.B.unswizzled_sTile, mos.B.mma_FrgThr);
    EXPECT_TRUE((std::is_same<std::remove_cv_t<decltype(ldsm_atom_A)>, 
                Copy_Atom<SM75_U16x4_LDSM_T, T>>::value)) << "LDSM atom A should be SM75_U16x4_LDSM_T";
    EXPECT_TRUE((std::is_same<std::remove_cv_t<decltype(ldsm_atom_B)>, 
                Copy_Atom<SM75_U16x2_LDSM_T, T>>::value)) << "LDSM atom B should be SM75_U16x2_LDSM_T";
}

// Now we double N tile, we should find the 16x4 atom for A and B as well
TEST(LDSMTest, tile_16_16_8_U16x4_T) {
    using T = half_t;
    using MNKPSlabShape = Shape<_64, _64, _64, _4>;
    using MNKTileShape = Shape<_16,_16,_8>;
    using ASlab = Layout<decltype(ABC_get_MNKP(A_t{}, MNKPSlabShape{}))>;
    using BSlab = Layout<decltype(ABC_get_MNKP(B_t{}, MNKPSlabShape{}))>;
    using CSlab = Layout<decltype(ABC_get_MNKP(C_t{}, MNKPSlabShape{}))>;

    auto mos = mosaic::make_mma_mosaic<T>(MNKTileShape{}, ASlab{}, BSlab{}, CSlab{});

    auto ldsm_atom_A = compatible_ldsm_atom<T>(mos.A.unswizzled_sTile, mos.A.mma_FrgThr);
    auto ldsm_atom_B = compatible_ldsm_atom<T>(mos.B.unswizzled_sTile, mos.B.mma_FrgThr);
    EXPECT_TRUE((std::is_same<std::remove_cv_t<decltype(ldsm_atom_A)>, 
                Copy_Atom<SM75_U16x4_LDSM_T, T>>::value)) << "LDSM atom A should be SM75_U16x4_LDSM_T";
    EXPECT_TRUE((std::is_same<std::remove_cv_t<decltype(ldsm_atom_B)>, 
                Copy_Atom<SM75_U16x4_LDSM_T, T>>::value)) << "LDSM atom B should be SM75_U16x4_LDSM_T";
}

// However, if we bump the mma atom placement to 1x2x1, we should find the 16x4 atom for A and 16x2 for B
TEST(LDSMTest, tile_16_16_8_MMA_1_2_1_U16x4_T) {
    using T = half_t;
    using MNKPSlabShape = Shape<_64, _64, _64, _4>;
    using MNKTileShape = Shape<_16,_16,_8>;
    using MMAAtomPlacement = Shape<_1,_2,_1>;
    using ASlab = Layout<decltype(ABC_get_MNKP(A_t{}, MNKPSlabShape{}))>;
    using BSlab = Layout<decltype(ABC_get_MNKP(B_t{}, MNKPSlabShape{}))>;
    using CSlab = Layout<decltype(ABC_get_MNKP(C_t{}, MNKPSlabShape{}))>;
    auto atom = default_MMA_atom<T>();
    auto mos = mosaic::make_mma_mosaic<T>(MNKTileShape{}, atom, MMAAtomPlacement{}, ASlab{}, BSlab{}, CSlab{});

    auto is_A_compatible = is_copy_atom_compatible(Copy_Atom<SM75_U16x4_LDSM_T, T>{}, mos.A.unswizzled_sTile, mos.A.mma_FrgThr);
    auto is_B_compatible = is_copy_atom_compatible(Copy_Atom<SM75_U16x2_LDSM_T, T>{}, mos.B.unswizzled_sTile, mos.B.mma_FrgThr);
    EXPECT_TRUE(is_A_compatible) << "LDSM atom A should be compatible";
    EXPECT_TRUE(is_B_compatible) << "LDSM atom B should be compatible";

    auto ldsm_atom_A = compatible_ldsm_atom<T>(mos.A.unswizzled_sTile, mos.A.mma_FrgThr);
    auto ldsm_atom_B = compatible_ldsm_atom<T>(mos.B.unswizzled_sTile, mos.B.mma_FrgThr);
    EXPECT_TRUE((std::is_same<std::remove_cv_t<decltype(ldsm_atom_A)>, 
                Copy_Atom<SM75_U16x4_LDSM_T, T>>::value)) << "LDSM atom A should be SM75_U16x4_LDSM_T";
    EXPECT_TRUE((std::is_same<std::remove_cv_t<decltype(ldsm_atom_B)>, 
                Copy_Atom<SM75_U16x2_LDSM_T, T>>::value)) << "LDSM atom B should be SM75_U16x2_LDSM_T";
}

// Now double the M tile and half the N tile, we should find the 16x8 atom for A and 16x2 for B
TEST(LDSMTest, tile_32_8_8_U16x8_and_U16x2_T) {
    using T = half_t;
    using MNKPSlabShape = Shape<_64, _64, _64, _4>;
    using MNKTileShape = Shape<_32,_8,_8>; 
    using ASlab = Layout<decltype(ABC_get_MNKP(A_t{}, MNKPSlabShape{}))>;
    using BSlab = Layout<decltype(ABC_get_MNKP(B_t{}, MNKPSlabShape{}))>;
    using CSlab = Layout<decltype(ABC_get_MNKP(C_t{}, MNKPSlabShape{}))>;

    auto mos = mosaic::make_mma_mosaic<T>(MNKTileShape{}, ASlab{}, BSlab{}, CSlab{});
    auto ldsm_atom_A = compatible_ldsm_atom<T>(mos.A.unswizzled_sTile, mos.A.mma_FrgThr);
    auto ldsm_atom_B = compatible_ldsm_atom<T>(mos.B.unswizzled_sTile, mos.B.mma_FrgThr);
    EXPECT_TRUE((std::is_same<std::remove_cv_t<decltype(ldsm_atom_A)>, 
                Copy_Atom<SM75_U16x8_LDSM_T, T>>::value)) << "LDSM atom A should be SM75_U16x8_LDSM_T";
    EXPECT_TRUE((std::is_same<std::remove_cv_t<decltype(ldsm_atom_B)>, 
                Copy_Atom<SM75_U16x2_LDSM_T, T>>::value)) << "LDSM atom B should be SM75_U16x2_LDSM_T";
}

// Now double the K tile and half the N tile, we should also find the 16x8 atom for A and 16x8 for B
TEST(LDSMTest, tile_16_8_32_U16x8_T) {
    using T = half_t;
    using MNKPSlabShape = Shape<_64, _64, _64, _4>;
    using MNKTileShape = Shape<_16,_8,_32>; 
    using ASlab = Layout<decltype(ABC_get_MNKP(A_t{}, MNKPSlabShape{}))>;
    using BSlab = Layout<decltype(ABC_get_MNKP(B_t{}, MNKPSlabShape{}))>;
    using CSlab = Layout<decltype(ABC_get_MNKP(C_t{}, MNKPSlabShape{}))>;
    auto mos = mosaic::make_mma_mosaic<T>(MNKTileShape{}, ASlab{}, BSlab{}, CSlab{});

    auto is_A_compatible = is_copy_atom_compatible(Copy_Atom<SM75_U16x8_LDSM_T, T>{}, mos.A.unswizzled_sTile, mos.A.mma_FrgThr);
    auto is_B_compatible = is_copy_atom_compatible(Copy_Atom<SM75_U16x8_LDSM_T, T>{}, mos.B.unswizzled_sTile, mos.B.mma_FrgThr);
    EXPECT_TRUE(is_A_compatible) << "LDSM atom A should be compatible";
    EXPECT_TRUE(is_B_compatible) << "LDSM atom B should be compatible";

    auto ldsm_atom_A = compatible_ldsm_atom<T>(mos.A.unswizzled_sTile, mos.A.mma_FrgThr);
    auto ldsm_atom_B = compatible_ldsm_atom<T>(mos.B.unswizzled_sTile, mos.B.mma_FrgThr);
    EXPECT_TRUE((std::is_same<std::remove_cv_t<decltype(ldsm_atom_A)>, 
                Copy_Atom<SM75_U16x8_LDSM_T, T>>::value)) << "LDSM atom A should be SM75_U16x8_LDSM_T";
    EXPECT_TRUE((std::is_same<std::remove_cv_t<decltype(ldsm_atom_B)>, 
                Copy_Atom<SM75_U16x8_LDSM_T, T>>::value)) << "LDSM atom B should be SM75_U16x8_LDSM_T";
}

// Now we introduce different major dims for A and B, for this case
// we should find the 16x4 atom for A and the 32x1 atom for B
TEST(LDSMTest, tile_16_8_8_U16x4_and_U32x1_T) {
    using T = half_t;
    using MNKTileShape = Shape<_16,_8,_8>;
    using ASlab = Layout<Shape<_64, _64, _4>, Stride<_1, _64, Int<4096>>>;
    using BSlab = Layout<Shape<_64, _64, _4>, Stride<_64, _1, Int<4096>>>;
    using CSlab = Layout<Shape<_64, _64, _4>, Stride<_64, _1, Int<4096>>>;

    auto mos = mosaic::make_mma_mosaic<T>(MNKTileShape{}, ASlab{}, BSlab{}, CSlab{});

    auto ldsm_atom_A = compatible_ldsm_atom<T>(mos.A.unswizzled_sTile, mos.A.mma_FrgThr);
    auto ldsm_atom_B = compatible_ldsm_atom<T>(mos.B.unswizzled_sTile, mos.B.mma_FrgThr);
    EXPECT_TRUE((std::is_same<std::remove_cv_t<decltype(ldsm_atom_A)>, 
                Copy_Atom<SM75_U16x4_LDSM_T, T>>::value)) << "LDSM atom A should be SM75_U16x4_LDSM_T";
    EXPECT_TRUE((std::is_same<std::remove_cv_t<decltype(ldsm_atom_B)>, 
                Copy_Atom<SM75_U32x1_LDSM_N, T>>::value)) << "LDSM atom B should be SM75_U32x1_LDSM_N";
}

// Now we double N tile, we should find the 16x4 atom for A and 32x2 for B
TEST(LDSMTest, tile_16_16_8_U16x4_and_U32x2_T) {
    using T = half_t;
    using MNKTileShape = Shape<_16,_16,_8>;
    using ASlab = Layout<Shape<_64, _64, _4>, Stride<_1, _64, Int<4096>>>;
    using BSlab = Layout<Shape<_64, _64, _4>, Stride<_64, _1, Int<4096>>>;
    using CSlab = Layout<Shape<_64, _64, _4>, Stride<_64, _1, Int<4096>>>;

    auto mos = mosaic::make_mma_mosaic<T>(MNKTileShape{}, ASlab{}, BSlab{}, CSlab{});

    auto ldsm_atom_A = compatible_ldsm_atom<T>(mos.A.unswizzled_sTile, mos.A.mma_FrgThr);
    auto ldsm_atom_B = compatible_ldsm_atom<T>(mos.B.unswizzled_sTile, mos.B.mma_FrgThr);
    EXPECT_TRUE((std::is_same<std::remove_cv_t<decltype(ldsm_atom_A)>, 
                Copy_Atom<SM75_U16x4_LDSM_T, T>>::value)) << "LDSM atom A should be SM75_U16x4_LDSM_T";
    EXPECT_TRUE((std::is_same<std::remove_cv_t<decltype(ldsm_atom_B)>, 
                Copy_Atom<SM75_U32x2_LDSM_N, T>>::value)) << "LDSM atom B should be SM75_U32x2_LDSM_N";
}

// Now we give it a different mma atom placement of 1x2x1, we should get the 16x4 atom for A and 32x1 for B
TEST(LDSMTest, tile_16_16_8_MMA_1_2_1_U16x4_and_U32x1_T) {
    using T = half_t;
    using MNKTileShape = Shape<_16,_16,_8>;
    using MMAAtomPlacement = Shape<_1,_2,_1>;
    using ASlab = Layout<Shape<_64, _64, _4>, Stride<_1, _64, Int<4096>>>;
    using BSlab = Layout<Shape<_64, _64, _4>, Stride<_64, _1, Int<4096>>>;
    using CSlab = Layout<Shape<_64, _64, _4>, Stride<_64, _1, Int<4096>>>;

    auto atom = default_MMA_atom<T>();
    auto mos = mosaic::make_mma_mosaic<T>(MNKTileShape{}, atom, MMAAtomPlacement{}, ASlab{}, BSlab{}, CSlab{});

    auto ldsm_atom_A = compatible_ldsm_atom<T>(mos.A.unswizzled_sTile, mos.A.mma_FrgThr);
    auto ldsm_atom_B = compatible_ldsm_atom<T>(mos.B.unswizzled_sTile, mos.B.mma_FrgThr);
    EXPECT_TRUE((std::is_same<std::remove_cv_t<decltype(ldsm_atom_A)>, 
                Copy_Atom<SM75_U16x4_LDSM_T, T>>::value)) << "LDSM atom A should be SM75_U16x4_LDSM_T";
    EXPECT_TRUE((std::is_same<std::remove_cv_t<decltype(ldsm_atom_B)>, 
                Copy_Atom<SM75_U32x1_LDSM_N, T>>::value)) << "LDSM atom B should be SM75_U32x1_LDSM_N";
}

// Now we double K tile, we should find the 16x8 atom for A and 32x4 for B
TEST(LDSMTest, tile_16_16_16_U16x8_and_U32x4_T) {
    using T = half_t;
    using MNKTileShape = Shape<_16,_16,_16>;
    using ASlab = Layout<Shape<_64, _64, _4>, Stride<_1, _64, Int<4096>>>;
    using BSlab = Layout<Shape<_64, _64, _4>, Stride<_64, _1, Int<4096>>>;
    using CSlab = Layout<Shape<_64, _64, _4>, Stride<_64, _1, Int<4096>>>;

    auto mos = mosaic::make_mma_mosaic<T>(MNKTileShape{}, ASlab{}, BSlab{}, CSlab{});

    auto ldsm_atom_A = compatible_ldsm_atom<T>(mos.A.unswizzled_sTile, mos.A.mma_FrgThr);
    auto ldsm_atom_B = compatible_ldsm_atom<T>(mos.B.unswizzled_sTile, mos.B.mma_FrgThr);
    EXPECT_TRUE((std::is_same<std::remove_cv_t<decltype(ldsm_atom_A)>, 
                Copy_Atom<SM75_U16x8_LDSM_T, T>>::value)) << "LDSM atom A should be SM75_U16x8_LDSM_T";
    EXPECT_TRUE((std::is_same<std::remove_cv_t<decltype(ldsm_atom_B)>, 
                Copy_Atom<SM75_U32x4_LDSM_N, T>>::value)) << "LDSM atom B should be SM75_U32x4_LDSM_N";
}

// Special case: should have 16x8 for A and B
TEST(LDSMTest, SpecialCase1) {
    using T = half_t;
    using MNKTileShape = Shape<Int<64>,Int<64>,Int<16>>;
    using ASlab = Layout<Shape<Int<2304>, Int<1024>, Int<128>>, Stride<_1, Int<2304>, Int<2359296>>>;
    using BSlab = Layout<Shape<_64, Int<1024>, Int<128>>, Stride<_1, _64, Int<65536>>>;
    using CSlab = Layout<Shape<Int<2304>, _64, Int<128>>, Stride<_64, _1, Int<147456>>>;

    auto mos = mosaic::make_mma_mosaic<T>(MNKTileShape{}, ASlab{}, BSlab{}, CSlab{});

    auto ldsm_atom_A = compatible_ldsm_atom<T>(mos.A.unswizzled_sTile, mos.A.mma_FrgThr);
    auto ldsm_atom_B = compatible_ldsm_atom<T>(mos.B.unswizzled_sTile, mos.B.mma_FrgThr);
    EXPECT_TRUE((std::is_same<std::remove_cv_t<decltype(ldsm_atom_A)>, 
                Copy_Atom<SM75_U16x8_LDSM_T, T>>::value)) << "LDSM atom A should be SM75_U16x8_LDSM_T";
    EXPECT_TRUE((std::is_same<std::remove_cv_t<decltype(ldsm_atom_B)>, 
                Copy_Atom<SM75_U16x8_LDSM_T, T>>::value)) << "LDSM atom B should be SM75_U16x8_LDSM_T";
}


// Special case for sympow_mma X0 d_tile 8, power 2
TEST(LDSMTest, SpecialCase2) {
    using T = half_t;
    using sTileLayout=Layout<tuple<C<8>, tuple<_16, _1>>, tuple<_1, tuple<C<8>, C<0>>>>;
    using FrgThr=Layout<
        tuple<tuple<_1, tuple<tuple<C<2L>, C<2L>>, _1>>, tuple<C<4L>, C<8>, tuple<_1, _1, _1>>>, tuple<tuple<C<0>, tuple<tuple<C<8L>, C<64L>>, C<0>>>, tuple<C<16L>, _1, tuple<C<0>, C<0>, C<0>>>>>;

    auto sTile = make_tensor<T>(coalesce_each(sTileLayout{}));
    using coalesced_frgThr = decltype(coalesce_each(FrgThr{}));
    using new_FrgThr = decltype(make_layout(fill_back<3>(unwrap_layout(select<0>(coalesced_frgThr{}))), unwrap_layout(select<1>(coalesced_frgThr{}))));

    auto frgThr = new_FrgThr{};
    auto is_compatible = is_ldsm_compatible<T>(product_each(shape(sTile)), sTile.layout(), frgThr);
    auto ldsm_atom = compatible_ldsm_atom<T>(sTile.layout(), frgThr);
    EXPECT_TRUE(is_compatible) << "LDSM atom should be compatible";
    EXPECT_TRUE((std::is_same<std::remove_cv_t<decltype(ldsm_atom)>, 
                Copy_Atom<SM75_U16x4_LDSM_T, T>>::value)) << "LDSM atom should be SM75_U16x4_LDSM_T";
}


// Special case for sympow_mma X1 d_tile 8, power 2
TEST(LDSMTest, SpecialCase3) {
    using T = half_t;
    using FrgThr=Layout<
        Shape<Shape<_8, Shape<Shape<_2, _2>, _1>>, Shape<_4, _8, Shape<_1, _1, _1>>>, 
        Stride<Stride<_1, Stride<Stride<_8, _64>, _0>>, Stride<_16, _0, Stride<_0, _0, _0>>>>;
    using STile = Layout<Shape<_64, _16>, Stride<_1, _64>>;

    auto result = is_copy_atom_compatible(Copy_Atom<SM75_U16x2_LDSM_T, T>{}, STile{}, FrgThr{});
    EXPECT_FALSE(result) << "LDSM atom should not be compatible";
}

// Special case for sympow_mma X1 d_tile 8, power 2
TEST(LDSMTest, SpecialCase4) {
    using T = bfloat16_t;
    using FrgThr=Layout<
        tuple<tuple<_1, tuple<tuple<C<2L>, C<2L>>, _1>>, tuple<C<4L>, C<8>, tuple<_1, _1, _1>>>, tuple<tuple<C<0>, tuple<tuple<C<8L>, C<64L>>, C<0>>>, tuple<C<16L>, _1, tuple<C<0>, C<0>, C<0>>>>>;
    using STile = Layout<Shape<_64, _16>, Stride<_1, _64>>;

    auto result = is_copy_atom_compatible(Copy_Atom<SM75_U16x2_LDSM_T, T>{}, STile{}, FrgThr{});
    EXPECT_TRUE(result) << "LDSM atom should be compatible";
}

// Failure case 1: tile size has a mode smaller than 8
TEST(LDSMTest, tile_16_8_8_bad_tile) {
    using T = half_t;
    using MNKTileShape = Shape<_16,_8,_8>;
    using ASlab = Layout<Shape<_64, _64, _4>, Stride<_1, _64, Int<4096>>>;
    using BSlab = Layout<Shape<_64, _64, _4>, Stride<_64, _1, Int<4096>>>;
    using CSlab = Layout<Shape<_64, _64, _4>, Stride<_64, _1, Int<4096>>>;

    auto mos = mosaic::make_mma_mosaic<T>(MNKTileShape{}, ASlab{}, BSlab{}, CSlab{});
    auto bad_stile_A = make_layout(Shape<_4, _16>{}, Stride<_1, _4>{});
    auto bad_stile_B = make_layout(Shape<_2, _16>{}, Stride<_1, _2>{});

    EXPECT_FALSE((is_ldsm_compatible<T>(bad_stile_A, mos.A.mma_FrgThr))) << "LDSM atom A should not be compatible";
    EXPECT_FALSE((is_ldsm_compatible<T>(bad_stile_B, mos.B.mma_FrgThr))) << "LDSM atom B should not be compatible";
}

TEST(LDSMTest, SpecialCase5) {
    using T=cutlass::bfloat16_t;
    constexpr bool use_ldsm=true;
    constexpr bool must_ldsm=false;
    using sTileLayout=cute::ComposedLayout<cute::Swizzle<3, 3, 3>, cute::C<0>, cute::Layout<cute::tuple<cute::C<32L>, cute::C<16L>>, cute::tuple<cute::C<16L>, cute::_1>>>;
    using sTileStorage=cute::ViewEngine<cute::smem_ptr<cutlass::bfloat16_t *>>;
    using FrgThr=cute::Layout<
        cute::tuple<cute::tuple<cute::_1, cute::_1, cute::C<16L>>, cute::tuple<cute::_1, cute::tuple<cute::C<32L>, cute::C<1L>, cute::_1>>>, cute::tuple<cute::tuple<cute::C<0>, cute::C<0>, cute::C<32L>>, cute::tuple<cute::C<0>, cute::tuple<cute::_1, cute::C<0>, cute::C<0>>>>>;
    using frgLayout=cute::Layout<cute::tuple<cute::_1, cute::_1, cute::C<16L>>, cute::tuple<cute::C<0>, cute::C<0>, cute::_1>>;
    using frgStorage=cute::ArrayEngine<cutlass::bfloat16_t, 16UL>;
    auto sTile = sTileLayout{};
    auto tiler = product_each(shape(sTile));
    auto frgThr = FrgThr{};
    auto ldsm_compatible = is_ldsm_compatible<T>(tiler, non_swizzled(sTile), frgThr);
    EXPECT_FALSE(ldsm_compatible) << "LDSM atom should not be compatible";
}

TEST(LDSMTest, SpecialCase6) {
    using Mosaic=mosaic::MmaMosaic_sm80<cutlass::half_t, cute::MMA_Atom<cute::SM80_16x8x8_F32F16F16F32_TN>, cute::tuple<cute::_16, cute::_16, cute::_16>, cute::tuple<cute::_1, cute::_2, cute::_1>, cute::Layout<cute::tuple<cute::_16, cute::_16, cute::_1>, cute::tuple<cute::_1, cute::_16, cute::C<0>>>, cute::Layout<cute::tuple<cute::_16, cute::_16, cute::_1>, cute::tuple<cute::_1, cute::_16, cute::C<0>>>, cute::Layout<cute::tuple<cute::_16, cute::_16, cute::_1>, cute::tuple<cute::_1, cute::_16, cute::C<0>>>, mosaic::DefaultPerf>;
    using rA_Engine=cute::ArrayEngine<cutlass::half_t, 8UL>;
    using rA_Layout=cute::Layout<cute::tuple<cute::tuple<cute::_2, cute::_2>, cute::_1, cute::_2>, cute::tuple<cute::tuple<cute::_1, cute::_2>, cute::C<0>, cute::_4>>;
    using rB_Engine=cute::ArrayEngine<cutlass::half_t, 4UL>;
    using rB_Layout=cute::Layout<cute::tuple<cute::_2, cute::_1, cute::_2>, cute::tuple<cute::_1, cute::_0, cute::_2>>;
    using sB_Engine=cute::ViewEngine<cute::smem_ptr<cutlass::half_t *>>;
    using sB_Layout=cute::Layout<cute::tuple<cute::C<16>, cute::C<16>>, cute::tuple<cute::_1, cute::_16>>;
    using rC_Engine=cute::ArrayEngine<float, 4UL>;
    using rC_Layout=cute::Layout<cute::tuple<cute::tuple<cute::_2, cute::_2>, cute::_1, cute::_1>, cute::tuple<cute::tuple<cute::_1, cute::_2>, cute::C<0>, cute::C<0>>>;

    Mosaic mos;
    auto is_B_compatible = is_copy_atom_compatible_debug(Copy_Atom<SM75_U16x8_LDSM_T, cutlass::half_t>{}, mos.B.unswizzled_sTile, mos.B.mma_FrgThr);
    print("mos.A.mma_FrgThr"); print(mos.A.mma_FrgThr); print("\n");
    print("mos.B.mma_FrgThr"); print(mos.B.mma_FrgThr); print("\n");
    print("mos.C.mma_FrgThr"); print(mos.C.mma_FrgThr); print("\n");
    EXPECT_FALSE(is_B_compatible) << "LDSM atom B should not be compatible";
}

} // namespace
} // namespace mosaic 