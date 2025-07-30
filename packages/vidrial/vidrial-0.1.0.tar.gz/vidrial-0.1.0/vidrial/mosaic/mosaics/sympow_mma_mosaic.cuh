#pragma once
#include "mma_mosaic.cuh"
#include "sympow_mosaic.cuh"
#include "../utils/allocator.cuh"

namespace mosaic {

template<typename T, int _pow, typename MmaAtom, typename MNKAtomPlacement, typename _MNKPSlabShape, typename MNKTileShape,
         int d, int _d_tile, bool _expand_K,
         typename _GaSlab, typename _GBSlab, typename _GCSlab, typename _PerfMosaic = DefaultPerf>
struct SympowMmaMosaic {
    static constexpr int pow = _pow;
    using GaSlab = decltype(static_tree_cast<int64_t>(_GaSlab{}));
    using GBSlab = decltype(static_tree_cast<int64_t>(_GBSlab{}));
    using GCSlab = decltype(static_tree_cast<int64_t>(_GCSlab{}));
    static constexpr bool expand_K = _expand_K;
    static constexpr int d_tile = _d_tile;
    using MNKPSlabShape = decltype(static_tree_cast<int64_t>(_MNKPSlabShape{}));
    static constexpr long M=get<0>(MNKPSlabShape{}),N=get<1>(MNKPSlabShape{}),K=get<2>(MNKPSlabShape{}),P=get<3>(MNKPSlabShape{}); 
    static constexpr long M_tile=get<0>(MNKTileShape{}),N_tile=get<1>(MNKTileShape{}),K_tile=get<2>(MNKTileShape{}); 
    static constexpr int D = expand_K?get<2>(MNKPSlabShape{}):get<0>(MNKPSlabShape{});
    static constexpr int D_tile = static_pow<pow>(d_tile);
    static_assert(D == sympow_dim<pow, d, d_tile>());
    static constexpr int expand_tile = expand_K?get<2>(MNKTileShape{}):get<0>(MNKTileShape{});
    static_assert(D_tile == expand_tile, "D_tile mismatch with MNKTileShape");
    static constexpr int D_tile_num = sympow_dim<pow, d/d_tile>();
    using PerfMosaic = _PerfMosaic;
    static constexpr PerfMosaic perf{};
    using ASlabShape = decltype(ABC_get_MNKP(A_t{}, MNKPSlabShape{}));
    using ATileShape = decltype(ABC_get_MNK(A_t{}, MNKTileShape{}));
    struct Mma2Sympow_expand_K { // K=D
        using aSlabShape = Shape<Int<M>,Int<d>,Int<P>>;
        using aTileShape = Shape<Int<d_tile>,Int<M_tile>>;
        using XSlabShape = Shape<Int<d>,Shape<Int<M>,Int<P>>>;
        using XTileShape = Shape<Int<d_tile>,Shape<Int<M_tile>,_1>>;
        using a2XSlab = decltype(select<1,0,2>(flatten(Layout<XSlabShape>{})));    // [M,d,P] -> [d,[M,P]]
        using X2aSlab = decltype(group<1,3>(select<1,0,2>(Layout<aSlabShape>{}))); // [d,[M,P]] -> [M,d,P]
        static_assert(rank(X2aSlab{}) == _2{});
        using a2XTile = decltype(select<1,0>(flatten(Layout<XTileShape>{})));      // [M_tile,d_tile] -> [d_tile,M_tile]
        using ZTileShape = decltype(tpow_shape<pow>(Shape<Int<d_tile>,Int<M_tile>>{}));
        using A2ZTile = decltype(select<1,0>(Layout<ZTileShape>{}));               // [M_tile,D_tile] -> [[d_tile,d_tile],M_tile]
        using ZSlabShape = decltype(static_tree_cast<int64_t>(Shape<Int<D>,Shape<Int<M>,Int<P>>>{})); // [D,[M,P]]
        using A2ZSlab = decltype(select<1,0,2>(flatten(Layout<ZSlabShape>{}))); // [M,D,P] -> [D,[M,P]]
    };
    struct Mma2Sympow_expand_M {
        using aSlabShape = Shape<Int<d>,Int<K>,Int<P>>;
        using aTileShape = Shape<Int<d_tile>,Int<K_tile>>;
        using XSlabShape = Shape<Int<d>,Shape<Int<K>,Int<P>>>;
        using XTileShape = Shape<Int<d_tile>,Shape<Int<K_tile>,_1>>;
        using a2XSlab = Layout<XSlabShape>; // [d,K,P] -> [d,[K,P]]
        using X2aSlab = decltype(group<1,3>(Layout<aSlabShape>{})); // [d,[K,P]] -> [d,K,P]
        using a2XTile = Layout<XTileShape>; // [d_tile,K_tile] -> [d_tile,K_tile]
        using A2ZTile = Layout<ATileShape>; // [D_tile,K_tile] -> [d_tile^p,K_tile]
        using ZSlabShape = decltype(static_tree_cast<int64_t>(Shape<Int<D>,Shape<Int<K>,Int<P>>>{})); // [D,[K,P]]
        using A2ZSlab = decltype(flatten(Layout<ZSlabShape>{})); // [D,K,P] -> [D,[K,P]]
    };
    using cnd = std::conditional_t<expand_K, Mma2Sympow_expand_K, Mma2Sympow_expand_M>;
    using a2XSlab = typename cnd::a2XSlab;
    using XSlabShape = typename cnd::XSlabShape;
    using XTileShape = typename cnd::XTileShape;
    using A2ZTile = typename cnd::A2ZTile;
    using X2aSlab = typename cnd::X2aSlab;
    using A2ZSlab = typename cnd::A2ZSlab;
    using ZTileShape = decltype(tpow_shape<pow>(XTileShape{}));

    using GXSlab = decltype(GaSlab{}.compose(X2aSlab{})); // gX_slab is a view of ga_slab
    using GZSlab = decltype(make_layout(static_tree_cast<int64_t>(sympow_shape<pow,d_tile>(XSlabShape{})))); // virtual
    using GASlab = decltype(GZSlab{}.compose(A2ZSlab{}));
    static_assert(size(GZSlab{}) == size(GASlab{}));
    using MmaMosaic = decltype(make_mma_mosaic<T, PerfMosaic, MmaAtom, MNKAtomPlacement>(MNKTileShape{}, MmaAtom{}, MNKAtomPlacement{}, GASlab{}, GBSlab{}, GCSlab{}));
    static constexpr MmaMosaic mma{};
    MmaAtom mma_Atom{};
    decltype(mma.A) A;
    decltype(mma.B) B;
    decltype(mma.C) C;
    using FrgTypeA = typename MmaMosaic::FrgTypeA;
    using FrgTypeB = typename MmaMosaic::FrgTypeB;
    using FrgTypeC = typename MmaMosaic::FrgTypeC;
    static constexpr int thread_num = mma.thread_num;
    static_assert(size(ZTileShape{}) == size(decltype(A){}.tileShape));
    using _ZMmaFrgThr = decltype(A2ZTile{}.compose(A.mma_FrgThr));
    using _ZTprodFrgThr = decltype(colayout(ZTileShape{}, get<0>(_ZMmaFrgThr{}))); // colayout transforms the mma_frg layout into a format compatible with tprod
    using ZTprodFrgThr = decltype(make_layout(_ZTprodFrgThr{}, get<1>(_ZMmaFrgThr{})));
    // using ATprodFrgThr_Frg = decltype(A2ZTile{}.compose(get<0>(ZTprodFrgThr{}))); // maps tprod_frg_coords -> A_coords
    using ATprodFrgThr_Frg = decltype(left_inverse(A2ZTile{}).compose(get<0>(ZTprodFrgThr{}))); // maps tprod_frg_coords -> A_coords
    using YTprod__2__AMma__frg = decltype(left_inverse(get<0>(A.mma_FrgThr)).compose(ATprodFrgThr_Frg{})); // A_tprod_frg_coords -> Y_tprod_frg_coords
    YTprod__2__AMma__frg Y_tprod_frg__2__A_mma_frg;
    using SZTile = Layout<ZTileShape>; // virtual (we don't even store the expansions in smem)
    using Sympow = SympowMosaic<T, pow, XSlabShape, XTileShape, ZTprodFrgThr, GZSlab, GXSlab, SZTile>;
    Sympow sympow;
    using SympowCoords = typename Sympow::SympowCoords;
    using Xi_t = decltype(typename Sympow::Xi_t{});
    Xi_t Xi;
    Sympow::XBatching X;
    Sympow::Y_t Y;
    Sympow::Z_t Z;
    using Xi_size_t = decltype(transform(Xi_t{}, [](auto const& x) { return size(x.sTile); }));
    using Xi_offset_t = decltype(get<1>(fold(Xi_size_t{}, make_tuple(_0{},make_tuple()),
            [](auto const& carry, auto const& Xi_size) {
                    auto [current, offsets] = carry;
                    return make_tuple(current+Xi_size, append(offsets, current)); })));
    using X_size_t = decltype(fold(Xi_size_t{}, _0{}, [](auto const& a, auto const& b) { return a + b; }));
    static constexpr Xi_size_t Xi_smem_size{};
    static constexpr Xi_offset_t Xi_smem_offset{};
    static constexpr X_size_t X_smem_size{};

    static int smem_size() {
        using AT = typename decltype(A)::T;
        using BT = typename decltype(B)::T;
        using CT = typename decltype(C)::T;
        using B_STile = typename decltype(B)::STile;
        using C_STile = typename decltype(C)::STile;
        using X_SBatch = decltype(X)::SXBatch;
        int ab_smem_size;
        if constexpr (expand_K) {
            ab_smem_size = Allocator<16>::total<AT, BT>(int(size(X_SBatch{})) * perf.smempipe, int(size(B_STile{})) * perf.smempipe);
        } else {
            ab_smem_size = Allocator<16>::total<AT, BT>(int(X_smem_size) * perf.smempipe, int(size(B_STile{})) * perf.smempipe);
        }
        int c_smem_size = Allocator<16>::total<CT>(int(size(C_STile{})));
        return static_max(ab_smem_size, c_smem_size);
    }
};


template<typename T, int _pow, typename MmaAtom, typename MNKAtomPlacement, typename _MNKPSlabShape, typename MNKTileShape,
         int d, int _d_tile, bool _expand_K,
         typename _GaSlab, typename _GBSlab, typename _GCSlab, typename _PerfMosaic>
void print_mosaic(SympowMmaMosaic<T, _pow, MmaAtom, MNKAtomPlacement, _MNKPSlabShape, MNKTileShape, d, _d_tile, _expand_K, _GaSlab, _GBSlab, _GCSlab, _PerfMosaic> const& mos, const char* prefix = "") {
    using Mosaic = SympowMmaMosaic<T, _pow, MmaAtom, MNKAtomPlacement, _MNKPSlabShape, MNKTileShape, d, _d_tile, _expand_K, _GaSlab, _GBSlab, _GCSlab, _PerfMosaic>;
    print(prefix); print("SympowMmaMosaic:\n");
    std::string prefix_str = std::string(prefix) + "  ";
    const char* _prefix = prefix_str.c_str();
    print(_prefix); print("pow: "); print(mos.pow); print("\n");
    print(_prefix); print("expand_K: "); print(mos.expand_K? "true" : "false"); print("\n");
    print(_prefix); print("M: "); print(Mosaic::M); print("\n");
    print(_prefix); print("N: "); print(Mosaic::N); print("\n");
    print(_prefix); print("K: "); print(Mosaic::K); print("\n");
    print(_prefix); print("P: "); print(Mosaic::P); print("\n");
    print(_prefix); print("D: "); print(Mosaic::D); print("\n");
    print(_prefix); print("M_tile: "); print(Mosaic::M_tile); print("\n");
    print(_prefix); print("N_tile: "); print(Mosaic::N_tile); print("\n");
    print(_prefix); print("K_tile: "); print(Mosaic::K_tile); print("\n");
    print(_prefix); print("D_tile: "); print(Mosaic::D_tile); print("\n");
    print(_prefix); print("thread_num: "); print(Mosaic::thread_num); print("\n");
    print(_prefix); print("XSlabShape: "); print(typename Mosaic::XSlabShape{}); print("\n");
    print(_prefix); print("XTileShape: "); print(typename Mosaic::XTileShape{}); print("\n");
    print(_prefix); print("ZTileShape: "); print(typename Mosaic::ZTileShape{}); print("\n");
    // Print transformations
    print(_prefix); print("a2XSlab: "); print(typename Mosaic::a2XSlab{}); print("\n");
    print(_prefix); print("X2aSlab: "); print(typename Mosaic::X2aSlab{}); print("\n");
    print(_prefix); print("A2ZSlab: "); print(typename Mosaic::A2ZSlab{}); print("\n");
    print(_prefix); print("A2ZTile: "); print(typename Mosaic::A2ZTile{}); print("\n");
    print(_prefix); print("Y_tprod_frg__2__A_mma_frg: "); print(mos.Y_tprod_frg__2__A_mma_frg); print("\n");
    // Print base MMA components
    print_mosaic(mos.mma, _prefix);
    // Print Sympow-specific components
    print_mosaic(mos.sympow, _prefix);
    print(_prefix); print("d: "); print(mos.D); print("\n");
    print(_prefix); print("d_tile: "); print(mos.D_tile); print("\n");
 
};

} // namespace mosaic