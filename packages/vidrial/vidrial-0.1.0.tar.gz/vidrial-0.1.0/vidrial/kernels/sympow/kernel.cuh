#pragma once
#include "../../mosaic/mosaics/sympow_mosaic.cuh"
#include "../../mosaic/utils/allocator.cuh"

namespace mosaic {

/* ----- sympow kernel -----
* Kernel uses dims d,b:
*   X_slab = [d,b]    X_tile = [d_tile,b_tile]
*   Z_slab = [D,b]  Z_tile = [D_tile,b_tile]
*   where D_tile = [d_tile,...]  (repeated power times)
*   and D = [D_tile,D_tile_num]
* The CTAs grid breaks appart the b dimension into b_tiles. Each CTA has a unique b_tile_idx
* During the mainloop D_tile_idx ranges from 0 -> D_tile_num-1
*   D_tile_idx can be thought of as a nondecreasing sequence of integers in range(0,d/d_tile)
*   with length power
*/
template <bool duplicate_correction, auto... Is, typename Mosaic, typename ZPtr, typename XPtr>
__device__ void tiled_sympow_kernel_impl(index_sequence<Is...>, Mosaic mos, ZPtr Z_ptr, XPtr X_ptr) {
    using T = typename Mosaic::T;
    int tid = threadIdx.x; int bid = blockIdx.x;
    auto sympow_coords = SympowCoords<Mosaic>{};
    sympow_coords.step_b(bid);
    auto gZ = make_tensor(make_gmem_ptr(Z_ptr), mos.Z.gSlab);
    auto gX = make_tensor(make_gmem_ptr(X_ptr), mos.X.gSlab);
    auto gX_batch = sympow_coords.slice_X_batch(gX); // [d, b_tile]
    alignas(16) __shared__ T Z_smem[int(cosize(mos.Z.sTile))]; // [[d_tile, d_tile, ...], b_tile]
    alignas(16) __shared__ T X_smem[int(cosize(mos.X.sBatch))]; // [d, b_tile]
    auto sZ_tile = make_tensor(make_smem_ptr(Z_smem), mos.Z.sTile); // [[d_tile, d_tile, ...], b_tile]
    auto sX_batch = make_tensor(make_smem_ptr(X_smem), mos.X.sBatch); // [d, b_tile]
    CTA_copy_tile(mos.X.batch_copy, gX_batch, sX_batch);
    cp_async_fence(); cp_async_wait<0>(); __syncthreads();
    auto sZ_copy_frg = slice_rest(sZ_tile, mos.Z.tile_copy.FrgThr, tid);
    auto rY_tprod_frg = make_tensor<T>(mos.Y.Frg);
    auto rXi_tprod_frg = make_tuple(make_tensor<T>(get<Is>(mos.Xi).Frg)...);
    while(sympow_coords.valid_D_tile()) {
        // Load the Xi_tiles from shared memory
        (..., [&]() {
            auto sXi_tile = sympow_coords.slice_X_tile_from_batch<Is>(sX_batch);
            auto sXi_tprod_frg = slice_rest(sXi_tile, get<Is>(mos.Xi).tprod_FrgThr, tid);
            copy(sXi_tprod_frg, get<Is>(rXi_tprod_frg));
        }());
        // Compute Z_tile as the tprod of the Xi_tiles
        tprod(rY_tprod_frg, get<Is>(rXi_tprod_frg)...);
        if constexpr (duplicate_correction)
            tensor_scalar_prod(rY_tprod_frg, static_cast<T>(sympow_coords.scale_correction()));
        copy(rY_tprod_frg, slice_rest(sZ_tile, mos.Y.tprod_FrgThr, tid));
        __syncthreads();
        // Write the Z_tile to global memory
        auto gZ_tile = sympow_coords.slice_Z_tile(gZ);
        CTA_copy_tile(mos.Z.tile_copy, sZ_tile, gZ_tile);
        // next iteration we are going to override sZ_tile. Sync to ensure no threads are sitill reading from it
        __syncthreads();
        sympow_coords.step_D();
    }
}
 
template <bool duplicate_correction, typename Mosaic, typename ZPtr, typename XPtr>
__global__ void tiled_sympow_kernel(Mosaic mos, ZPtr Z_ptr, XPtr X_ptr) {
    tiled_sympow_kernel_impl<duplicate_correction>(make_index_sequence<mos.p>{}, mos, Z_ptr, X_ptr);
}
template<bool duplicate_correction, typename Mosaic, typename ZPtr, typename XPtr>
void launch_tiled_sympow_kernel(Mosaic mos, ZPtr Z_ptr, XPtr X_ptr) {
    int blocks = int(size<1,1>(mos.Y.TileBlock));
    int threads = mos.thread_num;
    tiled_sympow_kernel<duplicate_correction><<<blocks, threads>>>(mos, Z_ptr, X_ptr);
}

} // namespace mosaic