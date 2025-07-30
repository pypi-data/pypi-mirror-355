#pragma once
#include "cute/tensor.hpp"
#include "copy.cuh"
#include "perf_mosaic.cuh"

namespace mosaic {

/*
 * A flavor of gemm algorithm that doesn't read all K frgments of B
 * into register, but pipeline the read.
 */
template<int pipe_size=1, typename Mosaic, typename rA_Engine, typename rA_Layout, typename rB_Engine, typename rB_Layout, typename sB_Engine, typename sB_Layout, typename rC_Engine, typename rC_Layout>
CUTE_DEVICE void gemm_impl(Mosaic const& mos, Tensor<rA_Engine, rA_Layout> const& rA_frg, Tensor<rB_Engine, rB_Layout> & rB_frg, Tensor<sB_Engine, sB_Layout> const& sB_tile, Tensor<rC_Engine, rC_Layout> &rC_frg)
{
    static_assert(is_smem<sB_Engine>::value,
                 "sB must be a smem-backed tensor");
    static_assert(!is_smem<rC_Engine>::value,
                 "rC must be a register-backed tensor");
    static_assert(!is_smem<rA_Engine>::value,
                 "rA must be a register-backed tensor");
    using T = typename sB_Engine::value_type;
    auto tid = threadIdx.x;
    auto result = slice_and_retile<T, mos.perf.use_ldsm>(sB_tile, mos.B.mma_FrgThr, rB_frg);
    auto copy_atom = std::get<0>(result); // might be a default copy atom or an ldsm atom
    auto sB_frg = std::get<1>(result); // sliced fragment of sB_tile
    auto rB_frg_copy = std::get<2>(result); // a retiled version of rB_frg, points to the same register, but it may have a larger V size than rB_frg if a large ldsm atom is used
    using rB_frg_copy_shape = decltype(rB_frg_copy.shape());
    using rB_frg_shape = decltype(rB_frg.shape());
    using rA_frg_shape = decltype(rA_frg.shape());
    CUTE_STATIC_ASSERT_V(size(rB_frg) == size(rB_frg_copy), "rB_frg and rB_frg_copy must have the same size");
    static_assert(size(rB_frg_copy_shape{}) % size(rB_frg_shape{}) == 0, "rB_frg_copy's per copy size must be a multiple of rB_frg's per k step size");
    static constexpr int copy_steps = size<2>(rB_frg_copy_shape{});
    static constexpr int iter_per_copy = size(rB_frg_copy_shape{}) / size(rB_frg_shape{});
    static constexpr int k_size = size<2>(rA_frg_shape{});
    static constexpr int k_size_B = size<2>(rB_frg_shape{}); // rB_frg's K size might be smaller than rA_frg's K size
    static constexpr int prefetch_iter = (copy_steps - pipe_size) * iter_per_copy;

    // prefetching
    CUTE_UNROLL
    for (int step = 0; step < static_min(pipe_size, copy_steps); step++) {
        copy(copy_atom, sB_frg(_, _, step), rB_frg_copy(_, _, step));
    }

    // main loop
    CUTE_UNROLL
    for (int i = 0, copy_step = 0; i < k_size; i++, copy_step = i / iter_per_copy) {
        if (i % iter_per_copy == 0 && i < prefetch_iter)
            copy(copy_atom, sB_frg(_, _, copy_step + pipe_size), rB_frg_copy(_, _, copy_step + pipe_size));
        cute::gemm(mos.mma_Atom, rA_frg(_, _, i), rB_frg(_, _, i % k_size_B), rC_frg);
    }
}


/*
 * Convenience dispatch for gemm 
 */
template<typename Mosaic, typename RA, typename RB, typename SB, typename RC>
CUTE_DEVICE void gemm(Mosaic const& mos, RA const& rA_frg, RB & rB_frg, SB & sB_tile, RC &rC_frg) {
    if constexpr (mos.perf.regpipe == 0) {
        cute::gemm(mos.mma_Atom, rA_frg, rB_frg, rC_frg);
    } else {
        mosaic::gemm_impl<mos.perf.regpipe>(mos, rA_frg, rB_frg, sB_tile, rC_frg);
    }
}


/*
 * Convenience dispatch for gemm, without having to create rB_frg up front. 
 * The advantage here is that we can minimize the register pressure by only
 * creating rB_frg of the size required by the regpipe size.
 */
template<typename Mosaic, typename RA, typename SB, typename RC>
CUTE_DEVICE void gemm(Mosaic const& mos, RA const& rA_frg, SB & sB_tile, RC &rC_frg) {
    using T = typename Mosaic::FrgTypeB;
    if constexpr (mos.perf.regpipe == 0) {
        auto rB_frg_mma = make_tensor<T>(mos.B.mma_Frg);
        load_frg<T, mos.perf.use_ldsm, sizeof(T) == 2>(sB_tile, mos.B.mma_FrgThr, rB_frg_mma);
        cute::gemm(mos.mma_Atom, rA_frg, rB_frg_mma, rC_frg);
    } else {
        using rB_frg_copy_t = decltype(get<2>(slice_and_retile<T, mos.perf.use_ldsm, sizeof(T) == 2>(sB_tile, mos.B.mma_FrgThr, make_tensor<T>(mos.B.mma_Frg))));
        constexpr auto ratio = size<2>(rB_frg_copy_t{}) / mos.perf.regpipe; // we can shrink the rB_frg by a factor of ratio
        using rB_frg_shape_t = decltype(append(select<0,1>(mos.B.mma_Frg), Int<get<2>(mos.B.mma_Frg) / ratio>{}));
        auto rB_frg = make_tensor<T>(make_layout(rB_frg_shape_t{}));
        mosaic::gemm_impl<mos.perf.regpipe>(mos, rA_frg, rB_frg, sB_tile, rC_frg);
    }
}

} // namespace mosaic