#pragma once
#include <iostream>
#include <optional>
#include <cute/tensor.hpp>
#include "../utils/utilities.cuh"
#include "../utils/tprod.cuh"
#include <cxxabi.h>

namespace mosaic {


// ------------- Helper Functions -------------
template<typename Shp, typename A, typename B, int max_element_size>
constexpr auto break_into_elements_impl() {
    constexpr auto contig_length_A = flat_major_dim_length(A{});
    constexpr auto contig_length_B = flat_major_dim_length(B{});
    constexpr int contig_length = static_min(contig_length_A, contig_length_B);
    constexpr int element_size = static_min(contig_length, max_element_size);
    constexpr auto upA = upcast<element_size>(A{});
    constexpr auto upB = upcast<element_size>(B{});
    constexpr auto upA_shp = transform_leaf(Shp{}, upA.shape(),
                    [](auto& s, auto& b) { return size(b);});
    constexpr auto upB_shp = transform_leaf(Shp{}, upB.shape(),
                    [](auto& s, auto& b) { return size(b);});
    constexpr bool shapes_match =fold(zip(upA_shp, upB_shp), true,
        [] (bool b, auto const& sizes) {return (get<0>(sizes)==get<1>(sizes)) ? b : false;});
    // If the shapes don't match we return the trivial elementing
    if constexpr (!shapes_match) {
        return tuple(Layout<Shp>{}, Layout<Shp>{}, 1);
    } else if constexpr (contig_length == contig_length_A) {
        return tuple(A{}, upA, element_size);
    } else if constexpr (contig_length == contig_length_B) {
        return tuple(B{}, upB, element_size);
    }
}
template<typename Shp, typename A, typename B, int max_element_size>
constexpr auto break_into_elements() {
    /* A,B are layouts maping shp_coords -> position. This function returns
    a layout that maps -> (v,r) -> shp_coord in a way that respects the contiguinty
    of the physical layouts A,B as much as possible. */
    if constexpr (!has_major_dim<A>() || !has_major_dim<B>()) {
        return make_layout(Layout<_1>{}, Layout<Shp>{});
    } else {
        constexpr auto res = break_into_elements_impl<Shp, A, B, max_element_size>();
        constexpr auto X = get<0>(res);
        constexpr auto fX = flatten(X);
        constexpr auto upfX = flatten(get<1>(res));
        constexpr auto element_size = Int<get<2>(res)>{};
        constexpr auto major_dim = flat_major_dim(fX);
        constexpr auto coord_str = make_layout(fX.shape()).stride();
        constexpr auto element_layout = make_layout(Int<element_size>{}, get<major_dim>(coord_str));
        constexpr auto rest_str = replace<major_dim>(coord_str, get<major_dim>(coord_str)*element_size);
        constexpr auto flat_rest_layout = make_layout(upfX.shape(), rest_str);
        constexpr auto rest_layout1 = unflatten(flat_rest_layout, X.shape());
        constexpr auto rest_layout2 = coalesce(rest_layout1, Shp{});
        return make_layout(element_layout, rest_layout2);
    }
}

/*
 * Breaks up the tile into fragments and assigns contiguous threads to each fragment.
 * If that doesn't cover the full tile the rest of the elements will be placed to the rest
 * modes of the fragment.
 * For a tile of shape [d1, d2], the frag shape will be [element_size, d1_rest, d2_rest]
 * The structure of the thread layout is independent of the tile dimensions.
 * The first dimension of the fragment is contiguous along both, the A,B layouts and
 * it is always less than max_element_size.
 * After mutual contiguity of the first fragment dimension, the threads prioritize
 * being contiguous along the A layout.
*/
template<int thread_num, int max_element_size, typename Shp, typename A, typename B>
auto maximally_contiguous_FrgThr(A const&, B const&) {
    constexpr auto elements = break_into_elements<Shp, A, B, max_element_size>();
    auto _rest = get<1>(elements); // We need to assign the rest modes among threads and fragment rest modes
    auto rest = sort_layout_by(A{}.stride(), _rest);
    auto recover_original_ordering = sort_by<LayoutStride(A), LayoutStride(Layout<LayoutShape(A)>)>();
    constexpr int copy_threads = gcd(thread_num, size(rest));
    auto [ThrShape, ___] = shape_minimum(rest.shape(), Int<copy_threads>{});
    auto Thr = coalesce(make_layout(ThrShape, rest.stride()));
    auto FrgRestShape = transform_leaf(rest.shape(), ThrShape,
                            [](auto& a, auto& b) {return a/b;});
    auto _FrgRestStride = elem_scale(rest.stride(), ThrShape);
    auto FrgRestStride = transform_leaf(FrgRestShape, _FrgRestStride,
        [](auto a, auto b) {return Int<(a>1)*b>{};});
    auto _FrgRest = make_layout(FrgRestShape, FrgRestStride);
    auto __FrgRest = sort_layout_by(recover_original_ordering, _FrgRest);
    auto FrgRest = unflatten(__FrgRest, Shp{});
    auto Frg = prepend(FrgRest, get<0>(elements));
    auto FrgThr = make_layout(Frg, Thr);
    filter(FrgThr);
    return FrgThr;
}

template<typename GSlab, typename TileShape>
auto default_sTile(GSlab gSlab, TileShape tileShape){
    /* It might seem that a reasonable choice would be for sTile to be column
    major but in many cases that would result in non vectorized copies.
    This sTle layout to match the contiguous dimension of gSlab */
    static_assert(rank(gSlab) == rank(tileShape), "gSlab and tileShape must have the same rank");
    static_assert(evenly_divides(gSlab, tileShape), "tileShape must evenly divide gSlab");
    auto gTileLayout = get<0>(zipped_divide(gSlab, tileShape));
    if constexpr (has_major_dim<decltype(gTileLayout)>()) {
        auto flat_gTileLayout = flatten(gTileLayout);
        constexpr auto major_dim = flat_major_dim(flat_gTileLayout);
        constexpr auto perm_shp = tuple_permute<0,major_dim>(flat_gTileLayout.shape());
        constexpr auto perm_layout = make_layout(perm_shp);
        constexpr auto flat_sTile = make_layout(flat_gTileLayout.shape(), tuple_permute<0,major_dim>(perm_layout.stride()));
        auto sTile = unflatten(flat_sTile, tileShape);
        return sTile;
    } else {
        return make_layout(tileShape);
    }
}
 

// assumes S and D tensors are the same shape and type
template<typename _T, int _thread_num, typename _TileShape,
         typename _GTile, typename _STile>
struct CopyMosaic_sm80 {
    using T = _T;
    static_assert(_thread_num <= 1024, "CUDA supports a maximum of 1024 threads per block");
    using ThreadNum = Int<_thread_num>;
    static constexpr ThreadNum thread_num = ThreadNum{};
    using TileShape = _TileShape;
    using GTile = _GTile;
    using STile = _STile;
    template<typename STile>
    struct get_layout_b {
        using type = decltype(STile{}.layout_b());
    };
    template<typename STile>
    struct return_self {
        using type = STile;
    };
    using STile_ = typename mosaic::lazy_conditional<is_composed_layout<STile>::value, get_layout_b<STile>, return_self<STile>>::type;

    // using GTile = decltype(static_tree_cast<int64_t>(_GTile{}));
    // using STile = decltype(static_tree_cast<int32_t>(_STile{}));
    GTile gTile{};
    STile sTile{};
    static constexpr int max_element_size = 16/sizeof(T); // at most we want16 bytes = 128 bits
    using FrgThr_t = decltype(maximally_contiguous_FrgThr<_thread_num, max_element_size,TileShape>(GTile{}, STile_{}));
    using Frg_t = decltype(make_layout(get<0>(FrgThr_t{}).shape()));
    FrgThr_t FrgThr;
    Frg_t Frg;
    static constexpr int element_size = size<0>(Frg_t{});
    static constexpr int frag_size = size(Frg_t{});
    using copy_uint_t = uint_bit_t<8*sizeof(T)*element_size>;
    using CopyAtom = Copy_Atom<UniversalCopy<copy_uint_t>, T>;
    CopyAtom universal_atom;
    // The sm80 architecture only supports async g2s copies of 128 contiguous bytes
    static constexpr bool g2s_is_async = sizeof(T) * element_size == 16 ? true : false;
    using _AsyncCopy = Copy_Atom<SM80_CP_ASYNC_CACHEGLOBAL<uint128_t>, T>;
    using G2SCopyAtom = std::conditional_t<g2s_is_async, _AsyncCopy, CopyAtom>;
    G2SCopyAtom g2s_atom;
};



template<typename T, int thread_num, typename TileShape, typename GTile, typename STile>
CUTE_HOST_DEVICE void CTA_copy_tile(CopyMosaic_sm80<T, thread_num, TileShape, GTile, STile>& mos,
                                    auto& S_tile, auto& D_tile) {
    using Mosaic = remove_cvref_t<decltype(mos)>;
    constexpr bool S_is_gmem = is_gmem<remove_cvref_t<decltype(S_tile)>>::value;
    constexpr bool D_is_smem = is_smem<remove_cvref_t<decltype(D_tile)>>::value;
    constexpr bool g2s_copy = S_is_gmem && D_is_smem;
    using CopyAtom = std::conditional_t<g2s_copy,
                                        typename Mosaic::G2SCopyAtom,
                                        typename Mosaic::CopyAtom>;
    if (threadIdx.x < size<1>(mos.FrgThr))
        copy(CopyAtom{},
             slice_rest(S_tile, mos.FrgThr, threadIdx.x),
             slice_rest(D_tile, mos.FrgThr, threadIdx.x));
}




// ------------- Tiling Mosaic -------------



template<typename _T, int _thread_num,
         typename _SlabShape, typename _TileShape,
         typename _GSlab, typename _STile, bool swizzle = false>
struct TilingMosaic_sm80 {
    using T = _T;
    using ThreadNum = Int<_thread_num>;
    static constexpr ThreadNum thread_num = ThreadNum{};
    using SlabShape = _SlabShape;
    using TileShape = _TileShape;
    static_assert(evenly_divides(SlabShape{}, TileShape{}), "TileShape must evenly divide SlabShape");
    using GSlab = _GSlab;
    using GTile = decltype(get<0>(zipped_divide(GSlab{}, TileShape{})));
    using STile = _STile;
    using TileBlock_t = decltype(zipped_divide(make_layout(SlabShape{}), TileShape{}));
    using TileCopy = CopyMosaic_sm80<T, thread_num, TileShape, GTile, STile>;
    GSlab gSlab;
    STile sTile;
    TileBlock_t TileBlock;
    TileCopy tile_copy;
};
template<typename _T, int _thread_num, typename SlabShape, typename TileShape,
         typename GSlab, typename STile>
auto make_tiling_mosaic(SlabShape slabShape, TileShape tileShape, GSlab gSlab, STile sTile){
    using Mosaic = TilingMosaic_sm80<_T, _thread_num, SlabShape, TileShape, GSlab, STile>;
    return Mosaic{};
}
template<typename _T, int _thread_num, typename SlabShape, typename TileShape, typename GSlab>
auto make_tiling_mosaic(SlabShape slabShape, TileShape tileShape, GSlab gSlab){
    auto sTile = default_sTile(gSlab, tileShape);
    return make_tiling_mosaic<_T, _thread_num>(slabShape, tileShape, gSlab, sTile);
}

template<typename _T, int _thread_num,
         typename _SlabShape, typename _TileShape,
         typename GSSlab, typename GDSlab>
struct MoveMosaic_sm80 {
    using T = _T;
    using ThreadNum = Int<_thread_num>;
    static constexpr ThreadNum thread_num = ThreadNum{};
    using SlabShape = _SlabShape;
    using TileShape = _TileShape;
    // sTile prioritizes 128 bit vectorization of the source->slab copy. More likely that g2s can be async
    using STile = decltype(default_sTile(GSSlab{}, TileShape{}));
    STile sTile;
    using S_t = TilingMosaic_sm80<T, _thread_num, SlabShape, TileShape, GSSlab, STile>;
    using D_t = TilingMosaic_sm80<T, _thread_num, SlabShape, TileShape, GDSlab, STile>;
    S_t S;
    D_t D;
    using Blocks_t = decltype(get<1>(S_t{}.TileBlock));
    Blocks_t Blocks;
};

// ------------- LDSM -------------
template<bool Transposed, typename _T>
using LDSM_ATOMS = std::conditional_t<Transposed,
    std::tuple<
        Copy_Atom<SM75_U16x8_LDSM_T, _T>,
        Copy_Atom<SM75_U16x4_LDSM_T, _T>,
        Copy_Atom<SM75_U16x2_LDSM_T, _T>,
    >,
    std::tuple<
        Copy_Atom<SM75_U32x4_LDSM_N, _T>,
        Copy_Atom<SM75_U32x2_LDSM_N, _T>,
        Copy_Atom<SM75_U32x1_LDSM_N, _T>,
    >
>;


/*
 * Given a source sTile layout, a copy atom, a frgThr layout, and a thread index,
 * slice the source tile to obtain the source fragment for the given thread using
 * the copy atom.
 * 
 * @param sTile: (logical_coord) -> (physical_coord)
 * @param copy_atom: the copy atom to use
 * @param frgThr: (frg, thr) -> (logical_coord on sTile)
 * @param tid: the thread index to slice the source tile for
 * @return: (src_frg_val, src_frg_rest) -> (physical_coord on sTile)
 */
template<typename STile, typename CopyAtom, typename FrgThr, typename Idx>
constexpr auto slice_src_frg(STile sTile, CopyAtom copy_atom, FrgThr frgThr, Idx tid) {
    using AtomNumThr = decltype(size<0>(typename CopyAtom::ValLayoutRef{}));
    using AtomNumVal = decltype(size<1>(typename CopyAtom::ValLayoutRef{}));
    using AtomLayoutSrc = typename CopyAtom::ValLayoutSrc; // (src_thr,src_val) -> offset
    using AtomLayoutDst = typename CopyAtom::ValLayoutDst; // (dst_thr,dst_val) -> offset
    using NumThr = decltype(size<1>(FrgThr{}));
    // Step 1: slice the source tile to obtain src_frg
    constexpr auto src2dst = decltype(right_inverse(select<1,0>(AtomLayoutDst{})).compose(select<1,0>(AtomLayoutSrc{}))){};
    // (src_atom_frg, src_atom_thr) -> (dst_atom_frg, dst_atom_thr)
    constexpr auto trg_frgthr_tiled = decltype(zipped_divide(FrgThr{}, make_shape(AtomNumVal{}, AtomNumThr{}))){};
    // ((atom_frg, atom_thr), (rest_frg, rest_thr)) -> coord
    constexpr auto atom_frgthr_src = decltype(trg_frgthr_tiled.compose(src2dst, _)){};
    // ((src_atom_frg, src_atom_thr), (rest_frg, rest_thr)) -> coord
    // Don't coalesce atom_frg, we can coalesce threads since we'll slice it later
    constexpr auto src_frgthr = decltype(coalesce(zip(atom_frgthr_src), Shape<Shape<_1,_1>,_1>{})){};
    // ((src_frg, rest_frg), (src_thr, rest_thr)) -> coord
    return unwrap(sTile.compose(src_frgthr)(_, tid));
}

/*
 * Given a destination frgThr layout, a copy atom, and a target frg layout,
 * re-arrange the frg layout to match the copy atom's destination frgThr layout.
 * 
 * @param copy_atom: the copy atom to use
 * @param frgThr: (frg, thr) -> (logical_coord)
 * @param frg: (frg) -> (physical_coord on register)
 * @return: (dst_frg_val, dst_frg_rest) -> (physical_coord on register)
 */
template<typename CopyAtom, typename FrgThr, typename Frg>
constexpr auto retile_dst_frg(CopyAtom copy_atom, FrgThr frgThr, Frg frg) {
    using AtomNumThr = decltype(size<0>(typename CopyAtom::ValLayoutRef{}));
    using AtomNumVal = decltype(size<1>(typename CopyAtom::ValLayoutRef{}));
    using AtomLayoutSrc = typename CopyAtom::ValLayoutSrc; // (src_thr,src_val) -> offset
    using AtomLayoutDst = typename CopyAtom::ValLayoutDst; // (dst_thr,dst_val) -> offset

    using copy_frgthr = decltype(zipped_divide(FrgThr{}, make_shape(AtomNumVal{}, AtomNumThr{})));
    // ((copy_frg, copy_thr), (rest_frg, rest_thr)) -> coord
    using coord2frgthr = decltype(right_inverse(FrgThr{}));
    // (m, n) -> (frg, thr)
    using frgthr2frgthr = decltype(coord2frgthr{}.compose(copy_frgthr{}));
    // ((copy_frg, copy_thr), (rest_frg, rest_thr)) -> (frg, thr)
    using frgthr_frgthr = decltype(zip(frgthr2frgthr{}));
    // ((copy_frg, rest_frg), (copy_thr, rest_thr)) -> (frg, thr)
    using copyfrg2frg = decltype(get<0>(frgthr_frgthr{}));
    // (copy_frg, rest_frg) -> frg
    return Frg{}.compose(copyfrg2frg{});
}


/*
 * A generic way to testing whether a copy atom is compatible with a given frgThr.
 * A copy atom is compatible with a frgThr if the frgThr "perfectly contains" the atom's destination frgThr layout.
 * 
 * A layout a is said to "contain" another layout b if there exists an offset N s.t.
 * 
 *      a(i) = b(i) + N for all i in domain(b)
 * 
 * A layout is said to "perfectly contain" another layout if for all N s.t. N % size(b) == 0,
 * 
 *      a(i) = b(i) + N for all i in domain(b)
 * 
 * i.e., if we can "tile" layout b to form a layout that is equivalent to layout a, then layout a "perfectly contains" layout b.
 * 
 * TODO: Until we figure out how to write the above test generic way, we use the following
 *       implementation. 
 * 
 * The current implementation of testing the compatibility is to do a copy dry-run and return
 * false if any of the places where normal execution would raise a static assertion.
 */
template<typename CopyAtom, typename FrgThr, typename STile>
constexpr bool is_copy_atom_compatible(CopyAtom atom, STile sTile, FrgThr frgThr) {
    using T = typename CopyAtom::ValType;
    using Frg = decltype(get<0>(FrgThr{}));
    constexpr auto src_frg = slice_src_frg(sTile, atom, frgThr, Int<0>{});
    // using DstFrg = decltype(retile_dst_frg(atom, frgThr, Frg{}));
    constexpr auto dst_frg = retile_dst_frg(atom, frgThr, make_layout(Frg{}.shape()));

    // Step 0: check if there's cross-thread interference
    if constexpr (size(Frg{}) != size(dst_frg))
        return false;

    // Step 1: check if the src_frg and dst_frg are compatible with each other
    // * check if they have the same size of rest modes
    if constexpr (rank(src_frg) != rank(dst_frg))
        return false;
    constexpr int R = rank(src_frg);
    constexpr auto src_v = group<1,R>(src_frg);
    constexpr auto dst_v = group<1,R>(dst_frg);
    if constexpr (size<1>(src_v) != size<1>(dst_v))
        return false;
    constexpr auto dst_null = decltype(nullspace(layout<1>(decltype(dst_frg){}))){};
    constexpr auto dst_n = decltype(zipped_divide(dst_v, make_tile(shape<0>(dst_v), dst_null))){};
    constexpr auto src_n = decltype(zipped_divide(src_v, make_tile(shape<0>(src_v), dst_null))){};
    if constexpr (size<1>(dst_n) != size<1>(src_n))
        return false;
    if constexpr (decltype(cosize<0,1>(dst_n) != Int<1>{})::value)
        return false;
    if constexpr (decltype(cosize<0,1>(src_n) != Int<1>{})::value)
        return false;
    if constexpr (decltype(size<1,0>(dst_n) != Int<1>{})::value)
        return false;
    if constexpr (decltype(size<1,0>(src_n) != Int<1>{})::value)
        return false;
    constexpr auto dst_c = dst_n(make_coord(_, Int<0>{}),make_coord(Int<0>{},_));
    constexpr auto src_c = src_n(make_coord(_, Int<0>{}),make_coord(Int<0>{},_));
    if constexpr (decltype(size<1>(dst_c) != size<1>(src_c))::value)
        return false;
    if constexpr (decltype(shape<0>(dst_c) != shape<0>(dst_frg))::value)
        return false;
    if constexpr (decltype(shape<0>(src_c) != shape<0>(src_frg))::value)
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
    if constexpr ((size(rS) != cosize(rS)) || (size(rD) != cosize(rD)))
        return false;
    if constexpr (size(rS) != Int<RegNumSrc>{})
        return false;
    if constexpr (size(rD) != Int<RegNumDst>{})
        return false;
        
    return true;
}


// Implementation for when all conditions are met
template<typename T, typename Tiler, typename STile, typename FrgThr>
constexpr auto is_ldsm_compatible_impl(Tiler tiler, STile sTile, FrgThr frgThr) {
    constexpr bool expect_transpose = flat_major_dim(sTile) == 0;
    return any_of(LDSM_ATOMS<expect_transpose, T>{}, [&](auto atom) {
        if constexpr (is_copy_atom_compatible(atom, sTile, frgThr)) {
            return std::true_type{};
        } else {
            return std::false_type{};
        }
    });
}

// Main function that checks conditions first
template<typename T, typename Tiler, typename STile, typename FrgThr>
constexpr auto is_ldsm_compatible(Tiler tiler, STile sTile, FrgThr frgThr) {
    if constexpr (has_major_dim<STile>() && depth(STile{}) == 1 && rank(STile{}) == 2 && min(flatten(shape(STile{}))) % 8 == 0 && sizeof(T) == 2) {
        return is_ldsm_compatible_impl<T>(tiler, sTile, frgThr);
    } else {
        return false;
    }
}

// Convenience overload with 2 arguments
template<typename T, typename STile, typename FrgThr>
constexpr auto is_ldsm_compatible(STile sTile, FrgThr frgThr) {
    using Tiler = decltype(product_each(shape(STile{})));
    return is_ldsm_compatible<T>(Tiler{}, sTile, frgThr);
}

/*
 * Return the LDSM atom that is compatible with the source tile and frgThr, provided that it exists.
 */
template<typename T, typename Tiler, typename STile, typename FrgThr>
constexpr auto compatible_ldsm_atom(Tiler tiler, STile sTile, FrgThr frgThr) {
    constexpr bool expect_transpose = flat_major_dim(sTile) == 0;
    auto atom_idx = find_if(LDSM_ATOMS<expect_transpose, T>{}, [&](auto atom) {
        if constexpr (is_copy_atom_compatible(atom, sTile, frgThr)) {
            return std::true_type{};
        } else {
            return std::false_type{};
        }
    });
    if constexpr (atom_idx >= 0 && atom_idx < 3) {
        return std::get<atom_idx>(LDSM_ATOMS<expect_transpose, T>{});
    } else {
        return std::nullopt;
    }
}


template<typename T, typename STile, typename FrgThr>
constexpr auto compatible_ldsm_atom(STile sTile, FrgThr frgThr) {
    return compatible_ldsm_atom<T>(product_each(shape(sTile)), sTile, frgThr);
}


// ------------- Print Helper Functions -------------
template<typename _T, int _thread_num, typename _TileShape, typename _GTile, typename _STile>
void print_mosaic(CopyMosaic_sm80<_T, _thread_num, _TileShape, _GTile, _STile> const& mosaic, const char* prefix = "") {
    print(prefix); print("CopyMosaic_sm80:\n");
    std::string prefix_str = std::string(prefix) + "  ";
    const char* _prefix = prefix_str.c_str();
    print(_prefix); print("gTile:          "); print(mosaic.gTile); print("\n");
    print(_prefix); print("sTile:          "); print(mosaic.sTile); print("\n");
    print(_prefix); print("FrgThr:         "); print(mosaic.FrgThr); print("\n");
    print(_prefix); print("Frg:            "); print(mosaic.Frg); print("\n");
    int status;
    char* demangled_universal = abi::__cxa_demangle(typeid(mosaic.universal_atom).name(), nullptr, nullptr, &status);
    char* demangled_g2s = abi::__cxa_demangle(typeid(mosaic.g2s_atom).name(), nullptr, nullptr, &status);
    print(_prefix); print("universal_atom: "); print(demangled_universal); print("\n");
    print(_prefix); print("g2s_atom:       "); print(demangled_g2s); print("\n");
    free(demangled_universal);
    free(demangled_g2s);
    print(_prefix); print("thread_num:    "); print(mosaic.thread_num); print("\n");
    print(_prefix); print("element_size:  "); print(mosaic.element_size); print("\n");
    print(_prefix); print("frag_size:     "); print(mosaic.frag_size); print("\n");
    print(_prefix); print("g2s_async:     "); print(mosaic.g2s_is_async? "true" : "false"); print("\n");
}

} // namespace mosaic