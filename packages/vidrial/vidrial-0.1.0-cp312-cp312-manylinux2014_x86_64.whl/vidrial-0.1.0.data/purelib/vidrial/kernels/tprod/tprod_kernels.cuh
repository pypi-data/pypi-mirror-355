#pragma once
#include "../../mosaic/mosaics/tprod_mosaic.cuh"

namespace mosaic {

template <auto... Is, typename Mosaic, typename YPtr, typename... XiPtr>
__device__ void tiled_tensor_product_kernel_impl(index_sequence<Is...>, Mosaic mos, YPtr Y_ptr, XiPtr... Xi_ptr) {
    using T = typename Mosaic::T;
    int tid = threadIdx.x; int bid = blockIdx.x;
    auto gY = make_tensor(make_gmem_ptr(Y_ptr), mos.Y.gSlab);
    auto Xi_ptr_tuple = make_tuple(Xi_ptr...);
    auto gXi = make_tuple(make_tensor(make_gmem_ptr(get<Is>(Xi_ptr_tuple)), get<Is>(mos.Xi).gSlab)...);
    auto gY_tile = slice_rest(gY, mos.Y.TileBlock, bid);
    auto gXi_tile = make_tuple(slice_rest(get<Is>(gXi), get<Is>(mos.Xi).TileBlock, bid)...);
    constexpr int tile_size = int(size(get<0>(gXi_tile)));
    __shared__ T Xi_smem[tile_size*mos.tprod_rank];
    auto sXi_tile = make_tuple(make_tensor(make_smem_ptr(Xi_smem+Is*tile_size), get<Is>(mos.Xi).Tile)...);
    get<0>(mos.Xi);
    (..., [&]() {
        auto gXi_frg_g2s = slice_rest(get<Is>(gXi_tile), get<Is>(mos.Xi).tile_copy.FrgThr, tid);
        auto sXi_frg_g2s = slice_rest(get<Is>(sXi_tile), get<Is>(mos.Xi).tile_copy.FrgThr, tid);
        if (tid < size<1>(get<Is>(mos.Xi).tile_copy.FrgThr)) {
            copy(get<Is>(mos.Xi).tile_copy.g2s_atom, gXi_frg_g2s, sXi_frg_g2s);
        }
    }());
    cp_async_fence(); cp_async_wait<0>(); __syncthreads();
    auto rY_frg = make_tensor<T>(mos.Y.Frg);
    auto rXi_tprod_frg = make_tuple(make_tensor<T>(get<Is>(mos.Xi).Frg)...);
    (..., (copy(slice_rest(get<Is>(sXi_tile), get<Is>(mos.Xi).tprod_FrgThr, tid), get<Is>(rXi_tprod_frg))));
    tprod(rY_frg, get<Is>(rXi_tprod_frg)...);
    __shared__ T Y_smem[int(size(gY_tile))];
    auto sY_tile = make_tensor(make_smem_ptr(Y_smem), mos.Y.tile_copy.sTile);
    copy(rY_frg, slice_rest(sY_tile, mos.Y.tprod_FrgThr, tid));
    __syncthreads();
    if (tid < size<1>(mos.Y.tile_copy.FrgThr)) {
        copy(mos.Y.tile_copy.universal_atom,
             slice_rest(sY_tile, mos.Y.tile_copy.FrgThr, tid),
             slice_rest(gY_tile, mos.Y.tile_copy.FrgThr, tid));
    }
}
template <typename Mosaic, typename YPtr, typename... XiPtr>
__global__ void tiled_tensor_product_kernel(Mosaic mos, YPtr Y_ptr, XiPtr... Xi_ptr) {
    constexpr int rank = sizeof...(XiPtr);
    tiled_tensor_product_kernel_impl(make_index_sequence<rank>{}, mos, Y_ptr, Xi_ptr...);
}
auto launch_tiled_tensor_product(auto mos, auto Y_ptr, auto... Xi_ptr) {
    int num_blocks = size<1>(mos.Y.TileBlock);
    tiled_tensor_product_kernel<<<num_blocks, mos.Y.thread_num>>>(mos, Y_ptr, Xi_ptr...);
} 

// -------------- Deprecated non variadic kernels --------------

template <typename Mosaic, typename YPtr, typename X0Ptr, typename X1Ptr>
__global__ void deprecated_rank2_tiled_tensor_product_kernel(Mosaic mos, YPtr Y_ptr, X0Ptr X0_ptr, X1Ptr X1_ptr) {
    using T = typename Mosaic::T;
    int tid = threadIdx.x; int bid = blockIdx.x;
    auto gY = make_tensor(make_gmem_ptr(Y_ptr), mos.Y.gSlab);
    auto gX0 = make_tensor(make_gmem_ptr(X0_ptr), get<0>(mos.Xi).gSlab);
    auto gX1 = make_tensor(make_gmem_ptr(X1_ptr), get<1>(mos.Xi).gSlab);
    auto gY_tile = slice_rest(gY, mos.Y.TileBlock, bid);
    auto gX0_tile = slice_rest(gX0, get<0>(mos.Xi).TileBlock, bid);
    auto gX1_tile = slice_rest(gX1, get<1>(mos.Xi).TileBlock, bid);
    __shared__ T X0_smem[int(size(gX0_tile))];
    __shared__ T X1_smem[int(size(gX1_tile))];
    auto sX0_tile = make_tensor(make_smem_ptr(X0_smem), get<0>(mos.Xi).Tile);
    auto sX1_tile = make_tensor(make_smem_ptr(X1_smem), get<1>(mos.Xi).Tile);
    auto gX0_frg_g2s = slice_rest(gX0_tile, get<0>(mos.Xi).tile_copy.FrgThr, tid);
    auto sX0_frg_g2s = slice_rest(sX0_tile, get<0>(mos.Xi).tile_copy.FrgThr, tid);
    if (tid < size<1>(get<0>(mos.Xi).tile_copy.FrgThr))
        copy(get<0>(mos.Xi).tile_copy.g2s_atom, gX0_frg_g2s, sX0_frg_g2s);
    auto gX1_frg_g2s = slice_rest(gX1_tile, get<1>(mos.Xi).tile_copy.FrgThr, tid);
    auto sX1_frg_g2s = slice_rest(sX1_tile, get<1>(mos.Xi).tile_copy.FrgThr, tid);
    if (tid < size<1>(get<1>(mos.Xi).tile_copy.FrgThr))
        copy(get<1>(mos.Xi).tile_copy.g2s_atom, gX1_frg_g2s, sX1_frg_g2s);
    cp_async_fence(); cp_async_wait<0>(); __syncthreads();
    auto rY_frg = make_tensor<T>(mos.Y.Frg);
    auto rX0_tprod_frg = make_tensor<T>(get<0>(mos.Xi).Frg);
    auto rX1_tprod_frg = make_tensor<T>(get<1>(mos.Xi).Frg);
    copy(slice_rest(sX0_tile, get<0>(mos.Xi).tprod_FrgThr, tid), rX0_tprod_frg);
    copy(slice_rest(sX1_tile, get<1>(mos.Xi).tprod_FrgThr, tid), rX1_tprod_frg);
    tprod(rY_frg, rX0_tprod_frg, rX1_tprod_frg);
    __shared__ T Y_smem[int(size(gY_tile))];
    auto sY_tile = make_tensor(make_smem_ptr(Y_smem), mos.Y.tile_copy.sTile);
    copy(rY_frg, slice_rest(sY_tile, mos.Y.tprod_FrgThr, tid));
    __syncthreads();
    if (tid < size<1>(mos.Y.tile_copy.FrgThr)) {
        copy(mos.Y.tile_copy.universal_atom,
             slice_rest(sY_tile, mos.Y.tile_copy.FrgThr, tid),
             slice_rest(gY_tile, mos.Y.tile_copy.FrgThr, tid));
    }
}

auto launch_deprecated_rank2_tiled_tensor_product_kernel(auto mos, auto Y_ptr, auto X0_ptr, auto X1_ptr) {
    int num_blocks = size<1>(mos.Y.TileBlock);
    deprecated_rank2_tiled_tensor_product_kernel<<<num_blocks, mos.Y.thread_num>>>(mos, Y_ptr, X0_ptr, X1_ptr);
} 

} // namespace mosaic
