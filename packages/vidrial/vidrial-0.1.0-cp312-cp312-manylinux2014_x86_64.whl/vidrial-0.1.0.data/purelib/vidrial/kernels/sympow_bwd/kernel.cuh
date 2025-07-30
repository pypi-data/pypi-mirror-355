#pragma once
#include "../../mosaic/mosaics/sympow_mosaic.cuh"
#include "../../mosaic/utils/reduce.cuh"

namespace mosaic {

template <int dim, auto... Is, typename YTensor, typename XTensors>
CUTE_HOST_DEVICE void tprod_bcast_multiply_all_except(index_sequence<Is...>, YTensor& Y, const XTensors& Xs) {
    (..., [&]() {
        if constexpr (Is != dim)
            tprod_bcast_multiply<Is>(Y, get<Is>(Xs));
    }());
}

template <int dim, typename YTensor, typename XTensors>
CUTE_HOST_DEVICE void tprod_bcast_multiply_all_except(YTensor& Y, const XTensors& Xs) {
    constexpr int rnk = rank(decltype(Xs){});
    tprod_bcast_multiply_all_except<dim>(make_index_sequence<rnk>{}, Y, Xs);
}

template<auto... Is, typename Mosaic>
__device__ void CTA_tprod_bwd(Mosaic& mos, auto& rYgrad_tprod_frg, auto& rXi_tprod_frg, auto& Xigrad_copy_frg, int tid) {
    using T = TensorType(rYgrad_tprod_frg);
    using YTileShape = decltype(mos.Y.TileShape);
    using YTprodFrgThr = decltype(mos.Y.tprod_FrgThr);
    __shared__ T smem[tprod_rmem_reduce_buffer_size<YTileShape, YTprodFrgThr>()];
    (..., [&]() { // accumulate sXigrad for each factor
        auto rY_tprod_frg_buff = make_tensor<T>(mos.Y.Frg); // buffer so we can operate on rY_tprod_frg without losing the original
        copy(rYgrad_tprod_frg, rY_tprod_frg_buff);
        tprod_bcast_multiply_all_except<Is>(rY_tprod_frg_buff, rXi_tprod_frg);
        auto rXigrad_copy_frg_buff = make_tensor<T>(get<Is>(mos.Xi).tile_copy.Frg);
        using XCopyFrgThr = decltype(get<Is>(mos.Xi).tile_copy.FrgThr);
        // TODO: confirm that tprod_rmem_reduce is working properly with XCopyFrgThr
        tprod_rmem_reduce_sum<Is, YTileShape, YTprodFrgThr, XCopyFrgThr>(rY_tprod_frg_buff, rXigrad_copy_frg_buff, tid, smem);
        if (tid < size<1>(get<Is>(mos.Xi).tile_copy.FrgThr)) {
            add_tensor(get<Is>(Xigrad_copy_frg), rXigrad_copy_frg_buff);
        }
    }());
}

// -------------- Example Kernels using TprodMosaic --------------
template <bool duplicate_correction, auto... Is, typename Mosaic, typename XPtr, typename ZGradPtr, typename XGradPtr>
__device__ void tiled_sympow_bwd_kernel_impl(index_sequence<Is...>, Mosaic mos, XPtr X_ptr, ZGradPtr Zgrad_ptr, XGradPtr Xgrad_ptr) {
    using T = typename Mosaic::T;
    int tid = threadIdx.x; int bid = blockIdx.x;
    // ----- Iterators of the kernel -----
    auto sympow_tile_coords = SympowCoords<Mosaic>{};
    sympow_tile_coords.step_b(bid);
    // ------ Global memory slabs ------
    auto gX_slab = make_tensor(make_gmem_ptr(X_ptr), mos.X.gSlab);
    auto gZgrad_slab = make_tensor(make_gmem_ptr(Zgrad_ptr), mos.Z.gSlab);
    auto gXgrad_slab = make_tensor(make_gmem_ptr(Xgrad_ptr), mos.X.gSlab);
    auto gX_batch = sympow_tile_coords.slice_X_batch(gX_slab);
    // ------ Shared memory tensors ------
    __shared__ alignas(16) T Z_smem[int(cosize(mos.Z.sTile))];
    __shared__ alignas(16) T X_smem[int(cosize(mos.X.sBatch))];
    __shared__ alignas(16) T Xgrad_smem[int(cosize(mos.X.sBatch))];
    auto sZgrad_tile = make_tensor(make_smem_ptr(Z_smem), mos.Z.sTile);
    auto sX_batch = make_tensor(make_smem_ptr(X_smem), mos.X.sBatch);
    auto sXgrad_batch = make_tensor(make_smem_ptr(Xgrad_smem), mos.X.sBatch);
    CTA_copy_tile(mos.X.batch_copy, gX_batch, sX_batch);
    clear(sXgrad_batch); // clear the gradient accumulators
    cp_async_fence(); cp_async_wait<0>(); __syncthreads();
    auto sZgrad_copy_frg = slice_rest(sZgrad_tile, mos.Z.tile_copy.FrgThr, tid);
    auto rYgrad_tprod_frg = make_tensor<T>(mos.Y.Frg);
    while (sympow_tile_coords.valid_D_tile()) {
        auto gZgrad_tile = sympow_tile_coords.slice_Z_tile(gZgrad_slab);
        CTA_copy_tile(mos.Z.tile_copy, gZgrad_tile, sZgrad_tile);
        cp_async_fence(); cp_async_wait<0>(); __syncthreads(); // ensure the sZgrad_tile is ready
        // load the Zgrad_frg into registers (applying the duplicate correction if necessary)
        copy(slice_rest(sZgrad_tile, mos.Y.tprod_FrgThr, tid), rYgrad_tprod_frg);
        if constexpr (duplicate_correction)
            tensor_scalar_prod(rYgrad_tprod_frg, static_cast<T>(sympow_tile_coords.scale_correction()));
        // load the relevant Xi_frg into registers
        auto rXi_tprod_frg = make_tuple(make_tensor<T>(get<Is>(mos.Xi).Frg)...);
        (..., [&]() { // s2r load of Xi_tprod_frg. Could be optimized by only loading the Xi fragment when the index has changed
            auto sXi_tile = sympow_tile_coords.slice_X_tile_from_batch<Is>(sX_batch);
            auto sXi_tprod_frg = slice_rest(sXi_tile, get<Is>(mos.Xi).tprod_FrgThr, tid);
            copy(sXi_tprod_frg, get<Is>(rXi_tprod_frg));
        }());
        // slice the Xgrad fragments for accumulation
        auto sXigrad_copy_frg = make_tuple(slice_rest(sympow_tile_coords.slice_X_tile_from_batch<Is>(sXgrad_batch),
                                                      get<Is>(mos.Xi).tile_copy.FrgThr,
                                                      tid)...);
        CTA_tprod_bwd<Is...>(mos, rYgrad_tprod_frg, rXi_tprod_frg, sXigrad_copy_frg, tid);
        __syncthreads(); // sZgrad_tile cannot be overwritten until all threads have used it to compute their gradients 
        sympow_tile_coords.step_D();
    }
    auto gXgrad_batch = sympow_tile_coords.slice_X_batch(gXgrad_slab);
    CTA_copy_tile(mos.X.batch_copy, sXgrad_batch, gXgrad_batch);
}
template <bool duplicate_correction, typename Mosaic, typename XPtr, typename ZGradPtr, typename XGradPtr>
__global__ void tiled_sympow_bwd_kernel(Mosaic mos, XPtr X_ptr, ZGradPtr Zgrad_ptr, XGradPtr Xgrad_ptr) {
    tiled_sympow_bwd_kernel_impl<duplicate_correction>(make_index_sequence<mos.p>{}, mos, X_ptr, Zgrad_ptr, Xgrad_ptr);
}
template<bool duplicate_correction, typename Mosaic, typename XPtr, typename ZGradPtr, typename XGradPtr>
void launch_tiled_sympow_bwd_kernel(Mosaic mos, XPtr X_ptr, ZGradPtr Zgrad_ptr, XGradPtr Xgrad_ptr) {
    int blocks = int(size<1,1>(mos.Y.TileBlock));
    int threads = mos.thread_num;
    tiled_sympow_bwd_kernel<duplicate_correction><<<blocks, threads>>>(mos, X_ptr, Zgrad_ptr, Xgrad_ptr);
}

} // namespace mosaic