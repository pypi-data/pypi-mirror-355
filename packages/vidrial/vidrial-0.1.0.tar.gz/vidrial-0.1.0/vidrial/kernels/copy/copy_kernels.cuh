#pragma once
#include "../mosaics/copy_mosaic.cuh"

namespace mosaic {

// ------------- Example Kernels -------------
template<typename T, typename Mosaic>
__global__ void tensor_scalar_add_kernel(Mosaic mos, T* A_ptr, T* B_ptr, T scalar) {
    static_assert(is_same<T, typename Mosaic::T>::value);
    int tid = threadIdx.x; int bid = blockIdx.x;
    auto gA_slab = make_tensor(make_gmem_ptr(A_ptr), mos.gSlab);
    auto gA_tile = slice_rest(gA_slab, mos.TileBlock, bid);
    auto gB_slab = make_tensor(make_gmem_ptr(B_ptr), mos.gSlab);
    auto gB_tile = slice_rest(gB_slab, mos.TileBlock, bid);
    __shared__ T smem[int(size(mos.sTile))];
    auto sA_tile = make_tensor(make_smem_ptr(smem), mos.sTile);
    if (tid < size<1>(mos.tile_copy.FrgThr)) {
        copy(mos.tile_copy.g2s_atom,
            slice_rest(gA_tile, mos.tile_copy.FrgThr, tid),
            slice_rest(sA_tile, mos.tile_copy.FrgThr, tid));
        cp_async_fence(); cp_async_wait<0>(); __syncthreads();
        auto rA_frg = make_tensor<T>(mos.tile_copy.Frg);
        copy(slice_rest(sA_tile, mos.tile_copy.FrgThr, tid), rA_frg);
        add_tensor_scalar(rA_frg, scalar);
        copy(mos.tile_copy.universal_atom,
            rA_frg,
            slice_rest(gB_tile, mos.tile_copy.FrgThr, tid));
    }
}

// template<typename Mosaic, typename F, typename SPtr, typename DPtr>
// __global__ void out_of_place_elementwise_kernel(Mosaic mos, SPtr S_ptr, DPtr D_ptr) {
//     using T = typename Mosaic::T;
//     int tid = threadIdx.x; int bid = blockIdx.x;
//     auto gS_slab = make_tensor(make_gmem_ptr(S_ptr), mos.S.gSlab);
//     auto gD_slab = make_tensor(make_gmem_ptr(D_ptr), mos.D.gSlab);
//     auto gS_tile = slice_rest(gS_slab, mos.S.TileBlock, bid);
//     auto gD_tile = slice_rest(gD_slab, mos.D.TileBlock, bid);
//     __shared__ T smem[int(size(mos.sTile))];
//     auto s_tile = make_tensor(make_smem_ptr(smem), mos.sTile);
//     copy(mos.S.g2s_atom,
//         slice_rest(gS_tile, mos.S.FrgThr, tid),
//         slice_rest(sSD_tile, mos.S.FrgThr, tid));
//     cp_async_fence(); cp_async_wait<0>(); __syncthreads();
//     auto rD_frg = make_tensor<T>(mos.D.Frg);
//     copy(mos.D.universal_atom,
//          slice_rest(s_tile, mos.D.FrgThr, tid),
//          SDrD_frg);
//     copy(mosD.universal_atom,
//         F(rD_frg),
//         slice_rest(gD_tile, mosD.FrgThr, tid));
// }

template<typename Mosaic, typename SPtr, typename DPtr>
__global__ void tiled_move_kernel(Mosaic mos, SPtr S_ptr, DPtr D_ptr) {
    using T = typename Mosaic::T;
    int tid = threadIdx.x; int bid = blockIdx.x;
    auto gS_slab = make_tensor(make_gmem_ptr(S_ptr), mos.S.gSlab);
    auto gD_slab = make_tensor(make_gmem_ptr(D_ptr), mos.D.gSlab);
    auto gS_tile = slice_rest(gS_slab, mos.S.TileBlock, bid);
    auto gD_tile = slice_rest(gD_slab, mos.D.TileBlock, bid);
    __shared__ T smem[int(size(mos.sTile))];
    auto s_tile = make_tensor(make_smem_ptr(smem), mos.sTile);
    copy(mos.S.tile_copy.g2s_atom,
        slice_rest(gS_tile, mos.S.tile_copy.FrgThr, tid),
        slice_rest(s_tile, mos.S.tile_copy.FrgThr, tid));
    cp_async_fence(); cp_async_wait<0>(); __syncthreads();
    copy(mos.D.tile_copy.universal_atom,
         slice_rest(s_tile, mos.D.tile_copy.FrgThr, tid),
         slice_rest(gD_tile, mos.D.tile_copy.FrgThr, tid));
}

} // namespace mosaic