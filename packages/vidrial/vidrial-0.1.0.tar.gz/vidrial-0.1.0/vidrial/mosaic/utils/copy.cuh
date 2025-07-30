#pragma once
#include <cute/tensor.hpp>
#include "copy_mosaic.cuh"
#include "swizzle_mosaic.cuh"

namespace mosaic {

template<typename T, typename Tiler, typename STile, typename FrgThr, typename Frg>
CUTE_DEVICE auto slice_and_retile_impl(std::true_type /* is_ldsm_compatible */, Tiler tiler, STile sTile, FrgThr frgThr, Frg &frg) {
    auto copy_atom = compatible_ldsm_atom<T>(Tiler{}, non_swizzled(STile{}.layout()), FrgThr{});
    auto tiled_copy = make_tiled_copy_impl(copy_atom, select<1,0>(frgThr), tiler);
    auto thr_copy = tiled_copy.get_thread_slice(threadIdx.x);
    auto frg_retiled = thr_copy.retile_D(frg);
    return std::forward_as_tuple(tiled_copy, thr_copy.partition_S(sTile), frg_retiled);
}

template<typename T, typename Tiler, typename STile, typename FrgThr, typename Frg>
CUTE_DEVICE auto slice_and_retile_impl(std::false_type /* is_ldsm_compatible */, Tiler tiler, STile sTile, FrgThr frgThr, Frg &frg) {
    auto frg_retiled = make_tensor(frg.data(), frg.layout());
    return std::forward_as_tuple(DefaultCopy{}, slice_rest(sTile, frgThr, threadIdx.x), frg_retiled);
}

/*
 * Slice the source tile and retile the fragment in a ldsm-compatible way, this is useful
 * for register pipelining
 */
template<typename T, bool use_ldsm, bool must_ldsm=false, typename Tiler, typename STile, typename FrgThr, typename Frg>
CUTE_DEVICE auto slice_and_retile(Tiler tiler, STile sTile, FrgThr frgThr, Frg &frg) {
    constexpr auto ldsm_compatible = is_ldsm_compatible<T>(tiler, non_swizzled(sTile.layout()), frgThr);
    static_assert(ldsm_compatible || !must_ldsm, "LDSM is not compatible with the source tile and frgThr");
    CUTE_STATIC_ASSERT_V(shape(get<0>(frgThr)) == shape(frg), "get<0>(frgThr) and frg must have the same shape");
    return slice_and_retile_impl<T>(std::integral_constant<bool, ldsm_compatible && use_ldsm>{}, tiler, sTile, frgThr, frg);
}

template<typename T, bool use_ldsm, bool must_ldsm=false, typename STile, typename FrgThr, typename Frg>
CUTE_DEVICE auto slice_and_retile(STile sTile, FrgThr frgThr, Frg &frg) {
    auto tiler = product_each(shape(sTile));
    return slice_and_retile<T, use_ldsm, must_ldsm>(tiler, sTile, frgThr, frg);
}

/*
 * Generic copy implementation. To copy from source tile to dest reg requires 
 * 1. slice the source tile according to the atom's frgThr
 * 2. retile the fragment to be compatible with the atom's frgThr
 * 
 * Note: 
 * 1. tiler is currently unused because we assume the passed-in sTile is
 * already the source tile.
 * 2. There's no assumptions on the rest mode of frg, so it can't be used for
 * reg pipelining gemm. Refere to slice_and_retile() for a version that can
 * handle reg pipelining gemm.
 * 3. This function assumes that get<0>(frgThr) is contiguous along copy atom's boundary,
 * this means that an otherwise compatible frgThr might be rejected by this function.
 * 4. This function assumes that a thread in frgThr does not ended up needing an element
 * only available in another thread using the given copy atom. 
 * 5. This function does not try to change the frg's layout to meet dst vectorization requirement in some edge cases where not doing so prevents us from using the copy atom.
 */
template<typename T, typename Tiler, typename STile, typename FrgThr, typename Frg>
CUTE_DEVICE auto copy_impl(std::true_type /* is_ldsm_compatible */, Tiler tiler, STile sTile, FrgThr frgThr, Frg &frg) {
    auto copy_atom = compatible_ldsm_atom<T>(Tiler{}, non_swizzled(sTile.layout()), FrgThr{});
    using CopyAtom = decltype(copy_atom);
    using AtomNumThr = decltype(size<0>(typename CopyAtom::ValLayoutRef{}));
    using AtomNumVal = decltype(size<1>(typename CopyAtom::ValLayoutRef{}));
    using AtomLayoutSrc = typename CopyAtom::ValLayoutSrc; // (src_thr,src_val) -> offset
    using AtomLayoutDst = typename CopyAtom::ValLayoutDst; // (dst_thr,dst_val) -> offset
    // Step 1: slice the source tile to obtain src_frg
    auto src2dst = right_inverse(select<1,0>(AtomLayoutDst{})).compose(select<1,0>(AtomLayoutSrc{}));
    // (src_atom_frg, src_atom_thr) -> (dst_atom_frg, dst_atom_thr)
    auto trg_frgthr_tiled = zipped_divide(frgThr, make_shape(AtomNumVal{}, AtomNumThr{}));
    // ((atom_frg, atom_thr), (rest_frg, rest_thr)) -> coord
    auto atom_frgthr_src = trg_frgthr_tiled.compose(src2dst, _);
    // ((src_atom_frg, src_atom_thr), (rest_frg, rest_thr)) -> coord
    // Don't coalesce atom_frg, we can coalesce threads since we'll slice it later
    auto src_frgthr = coalesce(zip(atom_frgthr_src), Shape<Shape<_1,_1>,_1>{});
    // ((src_frg, rest_frg), (src_thr, rest_thr)) -> coord
    auto src_frg = slice_rest(sTile, src_frgthr, threadIdx.x);
    
    // Step 2: retile the register so that it matches the atom's frgThr
    auto copy_frgthr = zipped_divide(frgThr, make_shape(AtomNumVal{}, AtomNumThr{}));
    // ((copy_frg, copy_thr), (rest_frg, rest_thr)) -> coord
    auto coord2frgthr = right_inverse(frgThr);
    // (m, n) -> (frg, thr)
    auto frgthr2frgthr = coord2frgthr.compose(copy_frgthr);
    // ((copy_frg, copy_thr), (rest_frg, rest_thr)) -> (frg, thr)
    auto frgthr_frgthr = zip(frgthr2frgthr);
    // ((copy_frg, rest_frg), (copy_thr, rest_thr)) -> (frg, thr)
    auto copyfrg2frg = get<0>(frgthr_frgthr);
    // (copy_frg, rest_frg) -> frg
    auto dst_frg = frg.compose(copyfrg2frg);
    // (copy_frg, rest_frg)
    copy(copy_atom, src_frg, dst_frg);
}

template<typename T, typename Tiler, typename STile, typename FrgThr, typename Frg>
CUTE_DEVICE auto copy_impl(std::false_type /* is_ldsm_compatible */, Tiler tiler, STile sTile, FrgThr frgThr, Frg &frg) {
    if (threadIdx.x < size<1>(frgThr))
        copy(slice_rest(sTile, frgThr, threadIdx.x), frg);
}

/*
 * Try to use LDSM if possible, otherwise use default copy atom
 */
template<typename T, bool must_ldsm, typename Tiler, typename STile, typename FrgThr, typename Frg>
CUTE_DEVICE auto load_frg(Tiler tiler, STile sTile, FrgThr frgThr, Frg &frg) {
    // TODO: refactor loda_frg into a mosaic
    constexpr auto ldsm_compatible = is_ldsm_compatible<T>(tiler, non_swizzled(sTile.layout()), frgThr);
    static_assert(ldsm_compatible || !must_ldsm, "LDSM is not compatible with the source tile and frgThr");
    CUTE_STATIC_ASSERT_V(shape(get<0>(frgThr)) == shape(frg), "get<0>(frgThr) and frg must have the same shape");
    copy_impl<T, Tiler, STile, FrgThr>(std::integral_constant<bool, ldsm_compatible>{}, tiler, sTile, frgThr, frg);
}

template<typename T, bool must_ldsm, typename sTileLayout, typename sTileStorage, typename FrgThr, typename frgLayout, typename frgStorage>
CUTE_DEVICE void load_frg(Tensor<sTileStorage, sTileLayout> sTile, FrgThr frgThr, Tensor<frgStorage, frgLayout> &frg) {
    auto tiler = product_each(shape(sTile));
    load_frg<T, must_ldsm>(tiler, sTile, frgThr, frg);
}

template<typename T, bool use_ldsm, bool must_ldsm, typename sTileLayout, typename sTileStorage, typename FrgThr, typename frgLayout, typename frgStorage>
CUTE_DEVICE void load_frg(Tensor<sTileStorage, sTileLayout> sTile, FrgThr frgThr, Tensor<frgStorage, frgLayout> &frg) {
    if constexpr (use_ldsm) {
        auto tiler = product_each(shape(sTile));
        load_frg<T, must_ldsm>(tiler, sTile, frgThr, frg);
    } else {
        if (threadIdx.x < size<1>(frgThr))
            copy(slice_rest(sTile, frgThr, threadIdx.x), frg);
    }
}

template<typename T, bool must_ldsm, typename Tiler, typename sTileLayout, typename sTileStorage, typename FrgThr>
CUTE_DEVICE auto load_frg(Tiler tiler, Tensor<sTileStorage, sTileLayout> sTile, FrgThr frgThr) {
    auto frg = make_tensor<T>(make_layout(get<0>(frgThr).shape()));
    load_frg<T, must_ldsm>(tiler, sTile, frgThr, frg);
    return frg;
}

template<typename T, bool must_ldsm, typename sTileLayout, typename sTileStorage, typename FrgThr>
CUTE_DEVICE auto load_frg(Tensor<sTileStorage, sTileLayout> sTile, FrgThr frgThr) {
    auto tiler = product_each(shape(sTile));
    auto frg = make_tensor<T>(make_layout(get<0>(frgThr).shape()));
    return load_frg<T, must_ldsm>(tiler, sTile, frgThr, frg);
}

template<typename T, bool use_ldsm, bool must_ldsm, typename sTileLayout, typename sTileStorage, typename FrgThr>
CUTE_DEVICE auto load_frg(Tensor<sTileStorage, sTileLayout> sTile, FrgThr frgThr) {
    if constexpr (use_ldsm) {
        auto tiler = product_each(shape(sTile));
        auto frg = make_tensor<T>(make_layout(get<0>(frgThr).shape()));
        return load_frg<T, must_ldsm>(tiler, sTile, frgThr, frg);
    } else {
        auto frg = make_tensor<T>(make_layout(get<0>(frgThr).shape()));
        if (threadIdx.x < size<1>(frgThr))
            copy(slice_rest(sTile, frgThr, threadIdx.x), frg);
        return frg;
    }
}

} // namespace mosaic