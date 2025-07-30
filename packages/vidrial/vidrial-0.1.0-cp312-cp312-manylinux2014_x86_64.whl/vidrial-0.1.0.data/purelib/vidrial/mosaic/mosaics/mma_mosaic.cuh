#pragma once
#include <cute/tensor.hpp>
#include <iostream>
#include "../utils/tprod.cuh"
#include "../utils/ABC_utils.cuh"
#include "../utils/allocator.cuh"
#include "copy_mosaic.cuh"
#include "perf_mosaic.cuh"
#include "swizzle_mosaic.cuh"
namespace mosaic {

/*
 * MmaMNKCoords is a helper class that slices a tensor into tiles.
 * It is used to slice the A, B, and C tensors into tiles.
 * It is also used to step along the M, N, K, and P dimensions.
 * It is also used to check if the current coords have reached the end of the tensor.
 * It works with slabs of data that have a batch dimension at the end (eg A is [M,K,P])
 * The sliced tiles do not have a batch dimension.
 */
template<typename MNKTileShape>
struct MmaMNKCoords {
    static_assert(rank(MNKTileShape{}) == 3, "MNKTileShape must be 3D");
    static constexpr MNKTileShape MNK_tile_shape{};
    tuple<int,int,int,int> MNKP_coords {0, 0, 0, 0};
    CUTE_HOST_DEVICE MmaMNKCoords(MNKTileShape MNK_tile_shape) : MNKP_coords(0,0,0,0) {}
    // get the current coords
    CUTE_HOST_DEVICE auto M_coord() { return get<0>(MNKP_coords); }
    CUTE_HOST_DEVICE auto N_coord() { return get<1>(MNKP_coords); }
    CUTE_HOST_DEVICE auto K_coord() { return get<2>(MNKP_coords); }
    CUTE_HOST_DEVICE auto P_coord() { return get<3>(MNKP_coords); }
    // Use the current coords to slice A,B,C tiles 
    template<auto... Is>
    CUTE_HOST_DEVICE auto _slice_tile(auto& tensor) {
        auto tile_shape = make_tuple(get<Is>(MNK_tile_shape)..., _1{});
        auto tiled_tensor = zipped_divide(tensor, tile_shape);
        auto tile_with_batch = slice_rest(tiled_tensor, select<Is...,3>(MNKP_coords));
        return tile_with_batch(_,_,_0{}); // slice out the batch dimension (of size 1)
    }
    CUTE_HOST_DEVICE auto slice_A_tile(auto& A_tensor) { return _slice_tile<0,2>(A_tensor); } // MKP
    CUTE_HOST_DEVICE auto slice_B_tile(auto& B_tensor) { return _slice_tile<1,2>(B_tensor); } // NKP
    CUTE_HOST_DEVICE auto slice_C_tile(auto& C_tensor) { return _slice_tile<0,1>(C_tensor); } // MNP
    // Step the coordinates along any dimension
    CUTE_HOST_DEVICE void step_M(int step = 1) { get<0>(MNKP_coords) += step; }
    CUTE_HOST_DEVICE void step_N(int step = 1) { get<1>(MNKP_coords) += step; }
    CUTE_HOST_DEVICE void step_K(int step = 1) { get<2>(MNKP_coords) += step; }
    CUTE_HOST_DEVICE void step_P(int step = 1) { get<3>(MNKP_coords) += step; }
    // Check if the current coords have reached the end of the tensor
    CUTE_HOST_DEVICE bool valid_M_tile(int M) { return get<0>(MNKP_coords) * get<0>(MNKTileShape{}) < M; }
    CUTE_HOST_DEVICE bool valid_N_tile(int N) { return get<1>(MNKP_coords) * get<1>(MNKTileShape{}) < N; }
    CUTE_HOST_DEVICE bool valid_K_tile(int K) { return get<2>(MNKP_coords) * get<2>(MNKTileShape{}) < K; }
    CUTE_HOST_DEVICE bool valid_P_tile(int P) { return get<3>(MNKP_coords) < P; }
    // Reset the coordinates 0
    CUTE_HOST_DEVICE void reset() { MNKP_coords = make_tuple(0,0,0,0); }
    CUTE_HOST_DEVICE void reset_M() { get<0>(MNKP_coords) = 0; }
    CUTE_HOST_DEVICE void reset_N() { get<1>(MNKP_coords) = 0; }
    CUTE_HOST_DEVICE void reset_K() { get<2>(MNKP_coords) = 0; }
    CUTE_HOST_DEVICE void reset_P() { get<3>(MNKP_coords) = 0; }
};



template<typename _T, typename _ABC_t, typename _MmaAtom,
         typename _MNKTileShape, typename _MNKAtomPlacement, 
         typename _GSlab, typename _PerfMosaic = DefaultPerf>
struct ABC_Mosaic_sm80 {
    using T = _T;
    using ABC_t = _ABC_t;
    using MmaAtom = _MmaAtom;
    using MNKAtomPlacement = _MNKAtomPlacement;
    using GSlab = _GSlab;
    using PerfMosaic = _PerfMosaic;
    static constexpr PerfMosaic perf{};
    GSlab gSlab{};
    using MatrixShape = decltype(get<0>(GSlab{}.shape()));
    using BatchSize = decltype(size<1>(GSlab{}.shape()));
    using TileShape = decltype(ABC_get_MNK(ABC_t{}, _MNKTileShape{}));
    static_assert(rank(TileShape{}) == Int<2>{}, "TileShape must be 2D");
    static_assert(evenly_divides(LayoutShape(GSlab){}, TileShape{}), "TileShape must divide the GSlab");
    TileShape tileShape;
    using _TB = decltype(zipped_divide(make_layout(gSlab.shape()), append(tileShape,_1{})));
    using Blocks_t = decltype(get<1>(_TB{}));
    using TileBlock_t = decltype(make_layout(select<0,1>(get<0>(_TB{})),Blocks_t{}));
    Blocks_t Blocks{}; // bid -> g offset
    TileBlock_t TileBlock{};  // tile_cord, bid -> g offset
    // ---------- MMA Op ----------
    MmaAtom mma_Atom;
    using AtomShape_t = decltype(ABC_get_MNK(ABC_t{}, typename MmaAtom::Shape_MNK{}));
    AtomShape_t AtomShape{};
    static_assert(get<2>(MNKAtomPlacement{}) == _1{}, "AtomPlacement K != 1 is tricky to implement. You need to accumulate the C registers. Remove assert only if your kernel supposrts it.");
    using AtomPlacement = decltype(ABC_get_MNK(ABC_t{}, MNKAtomPlacement{}));
    using VMNKThreads = decltype(tiled_product(typename MmaAtom::ThrID{}, Layout<MNKAtomPlacement>{}));
    static constexpr VMNKThreads Threads{};
    static constexpr int thread_num = size(Threads);
    using OpShape_t = decltype(elem_scale(AtomShape_t{}, AtomPlacement{}));
    static_assert(evenly_divides(TileShape{}, OpShape_t{}), "OpShape must divide the tileShape");
    static auto get_MmaOpFrgThr() {
        /* The Mma Op might use multiple atom placement (for CTAs with more threads than the atom) */
        auto AtomTV = ABC_get_TV_layout(ABC_t{}, MmaAtom{});
        auto AtomFrgThr = select<1,0>(AtomTV); // FrgThr layouts is just the transpose of ThrVal layouts
        auto OpLayoutMN = zipped_divide(make_layout(OpShape_t{}), AtomShape_t{});
        auto RestThreads = ABC_project_MNK(ABC_t{}, MNKAtomPlacement{});
        auto OpLayout_FT_MN = OpLayoutMN.compose(AtomFrgThr, RestThreads);
        auto OpLayoutF = get<0,0>(OpLayout_FT_MN);
        auto OpLayoutT = append(get<0,1>(OpLayout_FT_MN), get<1>(OpLayout_FT_MN));
        auto OpLayoutFT = make_layout(OpLayoutF, OpLayoutT);
        return OpLayoutFT;
    }
    using MmaOpFrgThr_t = decltype(get_MmaOpFrgThr());
    static auto get_MmaFrgThr() {
        /* The Tile Shape might be larger than the OpShape. The mma_FrgThr needs to tile*/
        auto tileLayout = make_layout(TileShape{});
        auto OpMN_RestMN= zipped_divide(tileLayout, OpShape_t{});
        auto OpFrgThr_RestMN = OpMN_RestMN.compose(MmaOpFrgThr_t{}, _); //  ((frg_v, tid), (tile_m, tile_n))
        auto OpFrgRestMN = prepend(get<1>(OpFrgThr_RestMN), get<0,0>(OpFrgThr_RestMN)); // (frg_v, tile_m, tile_n)
        auto OpFrgThr = make_layout(OpFrgRestMN, get<0,1>(OpFrgThr_RestMN)); // ((frg_v, tile_m, tile_n), tid)
        return OpFrgThr;
    }
    using MmaFrgThr = decltype(get_MmaFrgThr());
    using MmaFrg = decltype(make_layout(get<0>(MmaFrgThr{}.shape())));
    MmaFrgThr mma_FrgThr{};
    MmaFrg mma_Frg{};
    // ---------- G2S Copy ----------
    using GTile = decltype(get<0>(zipped_divide(select<0,1>(GSlab{}), TileShape{})));
    using STile_ = decltype(default_sTile(select<0,1>(GSlab{}), TileShape{}));
    using TileCopy = CopyMosaic_sm80<T, thread_num, TileShape, GTile, STile_>;

    // ---------- Swizzle ----------
    using UnswizzledSTile = STile_;
    using SwizzleMosaic_t = decltype(make_swizzle_mosaic<TileCopy, STile_, MmaFrgThr, perf.swizzle>(STile_{}, MmaFrgThr{}));
    using STile = SwizzleMosaic_t::SwizzledSTile;

    SwizzleMosaic_t swizzle_mos{};
    UnswizzledSTile unswizzled_sTile{};
    STile sTile{};
    GTile gTile{};
    TileCopy tile_copy;
    CUTE_HOST_DEVICE auto make_mma_frg() {
        using FrgType = typename ABC_FrgType<ABC_t, MmaAtom>::type;
        return make_tensor<FrgType>(mma_Frg);
    }
};

template<typename _T, typename _MmaAtom,
         typename _MNKTileShape, typename MNKAtomPlacement, 
         typename GASlab, typename GBSlab, typename GCSlab, typename _PerfMosaic = DefaultPerf>
struct MmaMosaic_sm80 {
    using T = _T;
    using MmaAtom = _MmaAtom;
    using MNKTileShape = _MNKTileShape;
    // using MNKPTileShape = decltype(append(MNKTileShape{}, _1{}));
    static_assert(is_static_v<MNKTileShape>, "MNKTileShape must be static");
    static constexpr MNKTileShape MNK_tile_shape{};
    // static constexpr MNKPTileShape MNKP_tile_shape{};
    MmaAtom mma_Atom;
    using AMosaic = ABC_Mosaic_sm80<T, A_t, MmaAtom, MNKTileShape, MNKAtomPlacement, GASlab, _PerfMosaic>;
    using BMosaic = ABC_Mosaic_sm80<T, B_t, MmaAtom, MNKTileShape, MNKAtomPlacement, GBSlab, _PerfMosaic>;
    using CMosaic = ABC_Mosaic_sm80<T, C_t, MmaAtom, MNKTileShape, MNKAtomPlacement, GCSlab, _PerfMosaic>;   
    using PerfMosaic = _PerfMosaic;
    static constexpr PerfMosaic perf{};
    AMosaic A;
    BMosaic B;
    CMosaic C;
    using FrgTypeA = typename MmaAtom::FrgTypeA;
    using FrgTypeB = typename MmaAtom::FrgTypeB;
    using FrgTypeC = typename MmaAtom::FrgTypeC;
    typename AMosaic::VMNKThreads Threads{};
    static constexpr int thread_num = AMosaic{}.thread_num;
    typename CMosaic::Blocks_t Blocks{};
    static constexpr int M = size<0>(typename AMosaic::GSlab{});
    static constexpr int N = size<0>(typename BMosaic::GSlab{});
    static constexpr int K = size<1>(typename AMosaic::GSlab{});
    static constexpr int P = size<2>(typename AMosaic::GSlab{});
    static constexpr int M_tile = size<0>(typename AMosaic::TileShape{});
    static constexpr int N_tile = size<0>(typename BMosaic::TileShape{});
    static constexpr int K_tile = size<1>(typename AMosaic::TileShape{});
    static constexpr int M_tile_num = size<0>(typename AMosaic::Blocks_t{});
    static constexpr int N_tile_num = size<0>(typename BMosaic::Blocks_t{});
    static constexpr int K_tile_num = size<1>(typename AMosaic::Blocks_t{});
    static constexpr int P_tile_num = size<2>(typename AMosaic::Blocks_t{});
    // Deprecated naming scheme
    static constexpr int M_blocks = size<0>(typename AMosaic::Blocks_t{});
    static constexpr int N_blocks = size<0>(typename BMosaic::Blocks_t{});
    static constexpr int K_blocks = size<1>(typename AMosaic::Blocks_t{});
    static constexpr int P_blocks = size<2>(typename AMosaic::Blocks_t{});

    static int smem_size() {
        using AT = typename AMosaic::T;
        using BT = typename BMosaic::T;
        using CT = typename CMosaic::T;
        using A_STile = typename AMosaic::STile;
        using B_STile = typename BMosaic::STile;
        using C_STile = typename CMosaic::STile;
        int ab_smem_size = Allocator<16>::total<AT, BT>(size(A_STile{}) * perf.smempipe, size(B_STile{}) * perf.smempipe);
        int c_smem_size = Allocator<16>::total<CT>(size(C_STile{}));
        return static_max(ab_smem_size, c_smem_size);
    }
};


// -------------- Make MmaMosaic --------------

template<typename T>
auto default_MMA_atom() {
    if constexpr(std::is_same_v<T, float>) {
        return MMA_Atom<SM80_16x8x8_F32TF32TF32F32_TN>{};
    } else if constexpr(std::is_same_v<T, half_t>) {
        return MMA_Atom<SM80_16x8x8_F32F16F16F32_TN>{};
    } else if constexpr(std::is_same_v<T, bfloat16_t>) {
        return MMA_Atom<SM80_16x8x8_F32BF16BF16F32_TN>{};
    } else {
        return UniversalFMA<T>{};
    }
}
// TODO: make a proper automatic system to pick MMA instructions, tileShapes and atom placements
template<typename T, typename _PerfMosaic=DefaultPerf, typename Atom, typename MNKAtomPlacement, typename MNKTileShape, 
         typename ASlab, typename BSlab, typename CSlab>
auto make_mma_mosaic(MNKTileShape, Atom, MNKAtomPlacement, ASlab, BSlab, CSlab) {
    return MmaMosaic_sm80<T, Atom, MNKTileShape, MNKAtomPlacement, ASlab, BSlab, CSlab, _PerfMosaic>{};
}
template<typename T, typename _PerfMosaic=DefaultPerf, typename Atom, typename MNKTileShape, 
         typename ASlab, typename BSlab, typename CSlab>
auto make_mma_mosaic(MNKTileShape, Atom, ASlab, BSlab, CSlab) {
    using MNKAtomPlacement = Shape<_1,_1,_1>;
    return MmaMosaic_sm80<T, Atom, MNKTileShape, MNKAtomPlacement, ASlab, BSlab, CSlab, _PerfMosaic>{};
}
template<typename T, typename _PerfMosaic=DefaultPerf, typename MNKTileShape, 
         typename ASlab, typename BSlab, typename CSlab>
auto make_mma_mosaic(MNKTileShape, ASlab, BSlab, CSlab) {
    auto atom = default_MMA_atom<T>();
    return make_mma_mosaic<T, _PerfMosaic>(MNKTileShape{}, atom, ASlab{}, BSlab{}, CSlab{});
}
template<typename T, typename MNKAtomPlacement=Shape<_1,_1,_1>, typename _PerfMosaic=DefaultPerf,
         typename ASlab, typename BSlab, typename CSlab>
auto make_mma_mosaic(ASlab, BSlab, CSlab) {
    using MNKTileShape = Shape<_16,_16,_16>;
    return make_mma_mosaic<T, _PerfMosaic>(MNKTileShape{}, ASlab{}, BSlab{}, CSlab{});
}

// ------------- Print Helper Functions -------------
template<typename _T, typename _ABC_t, typename _MmaAtom,
         typename _MNKTileShape, typename _MNKAtomPlacement, 
         typename _GSlab, typename _PerfMosaic>
void print_mosaic(ABC_Mosaic_sm80<_T, _ABC_t, _MmaAtom, _MNKTileShape, _MNKAtomPlacement, _GSlab, _PerfMosaic> const& mos, const char* prefix = "") {
    if constexpr(is_same_v<_ABC_t, A_t>) {
        print(prefix); print("A Mosaic:\n");
    } else if constexpr(is_same_v<_ABC_t, B_t>) {
        print(prefix); print("B Mosaic:\n");
    } else if constexpr(is_same_v<_ABC_t, C_t>) {
        print(prefix); print("C Mosaic:\n");
    }
    std::string prefix_str = std::string(prefix) + "  ";
    const char* _prefix = prefix_str.c_str();
    print(_prefix); print("gSlab: "); print(mos.gSlab); print("\n");
    print(_prefix); print("tileShape: "); print(mos.tileShape); print("\n");
    print(_prefix); print("TileBlock: "); print(mos.TileBlock); print("\n");
    print(_prefix); print("Blocks: "); print(mos.Blocks); print("\n");
    // print(_prefix); print("mma_AtomLayout: "); print(mos.mma_AtomLayout); print("\n");
    print(_prefix); print("Threads: "); print(mos.Threads); print("\n");
    print(_prefix); print("thread_num: "); print(mos.thread_num); print("\n");
    print(_prefix); print("mma_FrgThr: "); print(mos.mma_FrgThr); print("\n");
    print(_prefix); print("mma_Frg: "); print(mos.mma_Frg); print("\n");
    print_mosaic(mos.tile_copy, _prefix);
    print(_prefix); print("gTile: "); print(mos.gTile); print("\n");
    print(_prefix); print("sTile: "); print(mos.sTile); print("\n");
}
template<typename _T, typename _MmaAtom,
         typename _MNKTileShape, typename MNKAtomPlacement, 
         typename GASlab, typename GBSlab, typename GCSlab, typename _PerfMosaic>
void print_mosaic(MmaMosaic_sm80<_T, _MmaAtom, _MNKTileShape, MNKAtomPlacement, GASlab, GBSlab, GCSlab, _PerfMosaic> const& mos, const char* prefix = "") {
    print(prefix); print("MmaMosaic_sm80:\n");
    // print("  mma_atom: "); cute::print(abi::__cxa_demangle(typeid(mos.mma_Atom).name(), nullptr, nullptr, nullptr)); cute::print("\n");
    print_mosaic(mos.A, prefix);
    print_mosaic(mos.B, prefix);
    print_mosaic(mos.C, prefix);
}
} // namespace mosaic