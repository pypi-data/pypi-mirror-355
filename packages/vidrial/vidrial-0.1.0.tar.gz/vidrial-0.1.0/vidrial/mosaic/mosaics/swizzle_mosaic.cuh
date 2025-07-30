#pragma once
#include <cute/tensor.hpp>
#include <cute/numeric/integral_constant.hpp> 
#include "../utils/utilities.cuh"


namespace mosaic {
  using namespace cute;

template<typename T>
struct is_universal_copy : false_type {};

template<class S, class D>
struct is_universal_copy<UniversalCopy<S, D>> : true_type {};

template<int MaxVecBits>
struct is_universal_copy<AutoVectorizingCopyWithAssumedAlignment<MaxVecBits>> : true_type {};

/*
 * Given an sTile layout, convert it into a swizzled sTile layout. Here we make the following assumptions:
 * 1. The sTile layout is a row-major 2D layout (usually the case for A_Tile and B_Tile in cute)
 * 
 * 
 * 2^S cell per row─────────────────┐              
 * 2^M element per cell────┐        │              
 *                         ▼        ▼              
 *                       ┌───┐───┐───┐───┐───────┐ 
 *                       └───┘───┘───┘───┘       │ 
 *                       │                       │ 
 * 2^B rows per unit ◄── │                       │ 
 *                       │     Swizzle Unit      │ 
 *                       │                       │ 
 *                       │                       │ 
 *                       └───────────────────────┘ 
 * 
 */
template<typename G2SMosaic_, typename STile_, typename FrgThr_, int swizzle_mode=1>
struct SwizzleMosaic {
    /*
     * Find compatible copy atom to use
     */
    template<typename STile, typename FrgThr>
    static constexpr auto find_compatible_copy_atom() {
        if constexpr (is_ldsm_compatible<T>(STile{}, FrgThr{})) {
            return compatible_ldsm_atom<T>(STile{}, FrgThr{});
        } else {
            return DefaultCopy{};
        }
    }

    /*
     * Convert a frgThr layout into srcFrgThr layout
     */
    template<typename FrgThr, typename CopyAtom>
    static constexpr auto frgThr2srcFrgThr(std::false_type /* is_universal_copy */, FrgThr frgThr, CopyAtom) {
        using AtomNumVal = decltype(size<1>(typename CopyAtom::ValLayoutRef{}));
        using AtomNumThr = decltype(size<0>(typename CopyAtom::ValLayoutRef{}));
        using AtomLayoutSrc = typename CopyAtom::ValLayoutSrc; // (src_thr,src_val) -> offset
        using AtomLayoutDst = typename CopyAtom::ValLayoutDst; // (dst_thr,dst_val) -> offset
        constexpr auto src2dst = decltype(right_inverse(select<1,0>(AtomLayoutDst{})).compose(select<1,0>(AtomLayoutSrc{}))){};
        // (src_frg, rest_frg) -> (dst_frg, rest_frg)
        // assuming the trg2dst is contiguous within atom boundary
        constexpr auto trg_frgthr_tiled = zipped_divide(frgThr, make_shape(AtomNumVal{}, AtomNumThr{}));
        // ((atom_frg, atom_thr), (rest_frg, rest_thr)) -> coord
        constexpr auto src_frgthr_tiled = trg_frgthr_tiled.compose(src2dst, _);
        // ((atom_src_frg, atom_src_thr), (rest_frg, rest_thr)) -> coord
        constexpr auto src_frgthr = coalesce(zip(src_frgthr_tiled), Shape<Shape<_1,_1>,_1>{});
        // (src_frg, src_thr) -> coord
        return src_frgthr;
    }

    template<typename FrgThr, typename CopyAtom>
    static constexpr auto frgThr2srcFrgThr(std::true_type /* is_universal_copy */, FrgThr frgThr, CopyAtom) {
        return frgThr;
    }


    /*
    * Given a frgThr layout, we want to know for one round of copy operation,
    * what's the largest contiguous strip of indices to be copied across a warp.
    */
    template<typename FrgThr>
    static constexpr auto warp_contiguous_strip(FrgThr frgThr) {
        using SrcFrg = decltype(get<0>(frgThr));
        using SrcThr = decltype(get<1>(frgThr));
        using SrcWarp = decltype(get<0>(size_divide<32>(SrcThr{})));
        using ValWarp = decltype(make_layout(get<0>(SrcFrg{}), SrcWarp{}));
        return largest_contiguous_cosize(ValWarp{});
    }

    /*
     * Given a copy trait, extract the number of bytes to be copied
     */
    template<typename Struct>
    static constexpr auto copy_size(Copy_Traits<Struct>) {
        return sizeof(typename Struct::DRegisters{});
    }

    template<typename T, typename STile, typename SrcFrgThr, typename WriteAtom, bool write_optimized>
    static constexpr auto swizzled_sTile(STile sTile, SrcFrgThr read_FrgThr, WriteAtom write_atom){
        static_assert(rank(sTile) == 2, "sTile must be a 2D layout");
        static_assert(depth(sTile) == 1, "sTile must be a simple depth-1 stile to be swizzled");
        static_assert(has_major_dim<STile>(), "sTile must have a major dim");
        using TileShape = decltype(sTile.shape());
        constexpr auto write_bytes = copy_size(typename WriteAtom::Traits{});
        constexpr auto major_dim = flat_major_dim(STile{});
    
        // ---- Compute M
        // 2^M is the smallest un-swizzled sub-unit, so it matches the contiguous size of a single source fragment
        constexpr auto read_frg_major_mode = major_mode(get<0>(coalesce(read_FrgThr, Shape<Shape<_1,_1>,_1>{})));
        constexpr auto read_frg_contiguous_size = static_max(1, get<0>(read_frg_major_mode.shape()));
        constexpr auto write_size = write_bytes / sizeof(T);
        constexpr auto M = static_log2<static_max(read_frg_contiguous_size, write_size)>();

        // ---- Compute S
        // 2^(M+S) is the first index where swizzle starts, so it needs to cover, as contiguous as
        // possible, the first round of copy operation generated by all threads in a warp, subject 
        // to the limit that all 32 banks are fully utilized (128 bytes in total)
        constexpr auto read_warp_contiguous_size = size(warp_contiguous_strip(read_FrgThr));
        constexpr auto optimal_read_S = static_max(0, static_min(static_log2<static_max(128/sizeof(T), 1)>() - M, static_log2<static_max(read_warp_contiguous_size, 1)>() - M));
        constexpr auto optimal_write_S = static_max(0, static_log2<128/sizeof(T)>() - M);
        constexpr auto S = static_max(write_optimized ? optimal_write_S : optimal_read_S, 0);

        // ---- Compute B
        // 2^B is simply the number of times the warp_contiguous_strip needs to be tiled to cover
        // the entire sTile, subject to the limit that B <= M. If B is negative, we set it to 0 because
        // the tile is too small to be swizzled.
        constexpr auto B = static_max(static_min(static_log2<size(sTile)>() - S - M, S), 0);

        return Swizzle<Int<B>{}, Int<M>{}, Int<S>{}>{};
    }
    
    using G2SMosaic = G2SMosaic_;
    using T = typename G2SMosaic::T;
    using STile = STile_;
    using FrgThr = FrgThr_;
    static constexpr bool write_optimized = swizzle_mode == 1;
    using ReadAtom = decltype(find_compatible_copy_atom<STile, FrgThr>());
    using WriteAtom = typename G2SMosaic::G2SCopyAtom;
    ReadAtom read_atom{};
    WriteAtom write_atom{};

    using SrcFrgThr = decltype(frgThr2srcFrgThr(
            std::integral_constant<bool, is_universal_copy<ReadAtom>{}.value>(), 
            FrgThr{}, ReadAtom{}));
    static constexpr FrgThr frgThr{};
    static constexpr SrcFrgThr srcFrgThr{};
    static constexpr auto srcfrg_major_mode = major_mode(get<0>(coalesce(srcFrgThr, Shape<Shape<_1,_1>,_1>{})));
    static constexpr auto srcfrg_contiguous_size = static_max(1, get<0>(srcfrg_major_mode.shape()));
    static constexpr auto M = static_log2<srcfrg_contiguous_size>();
    using Swizzle_t = decltype(swizzled_sTile<T, STile, SrcFrgThr, WriteAtom, write_optimized>(STile{}, SrcFrgThr{}, write_atom));
    using SwizzledSTile = decltype(composition(Swizzle_t{}, STile{}));
    Swizzle_t swizzle{};
};

template<typename G2SMosaic_, typename STile_, typename FrgThr_>
struct NoSwizzle {
    using G2SMosaic = G2SMosaic_;
    using T = typename G2SMosaic::T;
    using STile = STile_;
    using FrgThr = FrgThr_;
    using SwizzledSTile = STile;
    using Swizzle_t = Swizzle<Int<0>{}, Int<0>{}, Int<0>{}>;
    Swizzle_t swizzle{};
};


template<typename G2SMosaic, typename STile, typename FrgThr, int swizzle_mode = 1,
         typename std::enable_if<(swizzle_mode == 1), int>::type = 0>
constexpr auto make_swizzle_mosaic(STile sTile, FrgThr frgThr) {
    return SwizzleMosaic<G2SMosaic, STile, FrgThr, swizzle_mode>{};
}

template<typename G2SMosaic, typename STile, typename FrgThr, int swizzle_mode = 0,
         typename std::enable_if<(swizzle_mode == 0), int>::type = 0>
constexpr auto make_swizzle_mosaic(STile sTile, FrgThr frgThr) {
    return NoSwizzle<G2SMosaic, STile, FrgThr>{};
}



// Primary template for types without layout_b()
template<typename Layout, typename = void>
struct NonSwizzledImpl {
    static constexpr auto apply(Layout layout) {
        return layout;
    }
};

// Specialization for types with layout_b()
template<typename Layout>
struct NonSwizzledImpl<Layout, std::void_t<decltype(Layout{}.layout_b())>> {
    static constexpr auto apply(Layout layout) {
        return layout.layout_b();
    }
};

// Single function that uses the implementation struct
template<typename Layout>
constexpr auto non_swizzled(Layout layout) {
    return NonSwizzledImpl<Layout>::apply(layout);
}

}// namespace mosaic

