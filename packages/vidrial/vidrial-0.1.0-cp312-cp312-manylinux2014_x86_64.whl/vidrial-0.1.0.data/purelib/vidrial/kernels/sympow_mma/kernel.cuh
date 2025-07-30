#pragma once
#include "sympow_mma_mosaic.cuh"
#include "../../mosaic/utils/pipeline.cuh"
#include "../../mosaic/utils/gemm.cuh"
#include "../../mosaic/utils/copy.cuh"
#include "../../mosaic/mosaics/perf_mosaic.cuh"
#include "../../mosaic/utils/allocator.cuh"
#include "../../mosaic/utils/launch.cuh"
namespace mosaic {


/* ----- fused sympow mma kernel -----
* Kernel uses 2 different coordinate systems for the 2 operations
*   dims M,N,K,P
*   A_slab = [M,K,P]  A_tile = [M_tile,K_tile]  A_tile = Z_tile
*   B_slab = [N,K,P]  B_tile = [N_tile,K_tile]
*   C_slab = [M,N,P]  C_tile = [M_tile,N_tile]
*   dims d,b: using d=M and b=[K,P]
*   X_slab = [d,b]    X_tile = [d_tile,b_tile]
*   Z_slab = [D,b]  Z_tile = [D_tile,b_tile]
*   where D_tile = [d_tile,...]  (repeated power times)
*   and D = [D_tile,d_tile_num]
* The two systems are connected via
*   D = M   and  b = [K,P]
*   so A_slab = [D,K,P],  Z_slab = [D,[K,P]], X_slab = [d,[K,P]]
*   A_tile = [D_tile,K_tile], Z_tile = [D_tile,K_tile], X_tile = [d_tile,K_tile]
* The CTAs grid works like in a standard tiled matmul kernel
*   CTA_idx = [M_tile_idx, N_tile_idx, P_tile_idx] (constant through execution)
*   so that each CTA computes a different C_tile
* During the mainloop:
*   K_tile_idx  ranges  0 -> mos.K_tile_num
*   b_tile_idx  ranges  [0, P_tile_idx] -> [mos.K_tile_num, P_tile_idx]
*/ 
template <bool duplicate_correction, auto... Is, typename Mosaic, typename AT, typename BT, typename CT>
__device__ void sympow_M_mma_kernel_impl(int_sequence<Is...>, Mosaic mos, AT* a_ptr, BT* B_ptr, CT* C_ptr) {
    static_assert(mos.expand_K==false, "This kernel is designed to expand M");
    int tid = threadIdx.x;
    int M_tile_idx = blockIdx.x;
    int N_tile_idx = blockIdx.y;
    int P_tile_idx = blockIdx.z;
    // ----- Iterators of the kernel: -----
    auto mma_tile_coords = MmaMNKCoords(mos.mma.MNK_tile_shape);
    mma_tile_coords.step_M(blockIdx.x);
    mma_tile_coords.step_N(blockIdx.y);
    mma_tile_coords.step_P(blockIdx.z);
    auto sympow_tile_coords = SympowCoords<decltype(mos.sympow)>{};
    sympow_tile_coords.step_D(M_tile_idx); // d_tile_idx = M_tile_idx
    sympow_tile_coords.step_b(mos.mma.K_tile_num * P_tile_idx); // b_tile_idx = [0,P_tile_idx]
    // ------ Global memory slabs ------
    auto gX_slab = make_tensor(make_gmem_ptr(a_ptr), mos.X.gSlab);
    auto gB_slab = make_tensor(make_gmem_ptr(B_ptr), mos.B.gSlab);
    auto gC_slab = make_tensor(make_gmem_ptr(C_ptr), mos.C.gSlab);
    // ------ Shared memory pipelines ------
    constexpr static int smempipe = static_min(mos.perf.smempipe, mos.mma.K_tile_num);
    auto pipe = SmemPipe<smempipe>();
    extern __shared__ char smem[];
    Allocator<16> alloc(smem);
    AT* Xi_smem = alloc.allocate<AT>(int(mos.X_smem_size) * smempipe);
    BT* B_smem = alloc.allocate<BT>(size(mos.B.sTile) * smempipe);
    auto sX_tile_pipes = make_tuple(pipe.create(Xi_smem, get<Is>(mos.Xi).sTile, get<Is>(mos.Xi).tile_copy, get<Is>(mos.Xi_smem_offset) * smempipe)...);
    auto sB_tile_pipe = pipe.create(B_smem, mos.B.sTile, mos.B.tile_copy);
    // ------ Register fragments for mma and tprod operations ------
    auto rA_frg_mma = mos.A.make_mma_frg();
    auto rB_frg_mma = mos.B.make_mma_frg();
    auto rC_frg_mma = mos.C.make_mma_frg();
    clear(rC_frg_mma);
    auto rXi_tprod_frg = make_tuple(make_tensor<AT>(get<Is>(mos.Xi).Frg)...);
    auto rY_tprod_frg = rA_frg_mma.compose(mos.Y_tprod_frg__2__A_mma_frg);
    using YFrgType = TensorType(rY_tprod_frg);
    YFrgType scale = static_cast<YFrgType>(sympow_tile_coords.scale_correction());
    // ------ Pipeline fetch X_tiles and B_tile ------
    auto pipe_fetch = [&]() {
        if (mma_tile_coords.K_coord() < mos.mma.K_tile_num) {
            auto gX_tiles = make_tuple(sympow_tile_coords.slice_X_tile<Is>(gX_slab)...);
            auto gB_tile = mma_tile_coords.slice_B_tile(gB_slab);
            pipe.fetch(gB_tile, sB_tile_pipe, mos.B.tile_copy);
            (..., pipe.fetch(get<Is>(gX_tiles), get<Is>(sX_tile_pipes), get<Is>(mos.Xi).tile_copy));
            mma_tile_coords.step_K();
            sympow_tile_coords.step_b();
        }
        pipe.commit();
    };
    // ------ Prefill pipeline ------
    for (; pipe.stage < smempipe - 1; pipe.step())
        pipe_fetch();
    // ------ Main loop ------
    for (int k_tile = 0; k_tile < mos.mma.K_tile_num; k_tile++) {
        pipe_fetch();
        pipe.ready();
        auto sB_tile = pipe.read(sB_tile_pipe);
        auto sX_tiles = make_tuple(coalesce_each(pipe.read(get<Is>(sX_tile_pipes)))...);
        (..., (load_frg<AT, mos.perf.use_ldsm, false>(get<Is>(sX_tiles), get<Is>(mos.Xi).tprod_FrgThr, get<Is>(rXi_tprod_frg))));
        if constexpr (mos.perf.regpipe == 0)
            load_frg<BT, mos.perf.use_ldsm, sizeof(BT) == 2>(sB_tile, mos.B.mma_FrgThr, rB_frg_mma);
        tprod(rY_tprod_frg, get<Is>(rXi_tprod_frg)...);
        if constexpr (duplicate_correction)
            tensor_scalar_prod(rY_tprod_frg, scale);
        mosaic::gemm(mos, rA_frg_mma, rB_frg_mma, sB_tile, rC_frg_mma);
        pipe.step();
    }
    pipe.finish();
    // ------ Write C_tile to global memory ------
    alloc.reset(smem);
    CT* C_smem = alloc.allocate<CT>(int(size(mos.C.sTile)));
    auto sC_tile = make_tensor(make_smem_ptr(C_smem), mos.C.sTile);
    copy(rC_frg_mma, slice_rest(sC_tile, mos.C.mma_FrgThr, tid));
    __syncthreads();
    auto gC_tile = mma_tile_coords.slice_C_tile(gC_slab);
    CTA_copy_tile(mos.C.tile_copy, sC_tile, gC_tile);
}
template <bool duplicate_correction, typename Mosaic, typename AT, typename BT, typename CT>
__global__ void sympow_M_mma_kernel(Mosaic mos, AT* a_ptr, BT* B_ptr, CT* C_ptr) {
    sympow_M_mma_kernel_impl<duplicate_correction>(make_int_sequence<mos.pow>{}, mos, a_ptr, B_ptr, C_ptr);
}

// ---- Expand the contraction dimension of the A matrix in the matmul -----
template <bool duplicate_correction, auto... Is, typename Mosaic, typename AT, typename BT, typename CT>
__device__ void sympow_K_mma_kernel_impl(int_sequence<Is...>, Mosaic mos, AT* a_ptr, BT* B_ptr, CT* C_ptr) {
    static_assert(mos.expand_K==true, "This kernel is designed to expand K");
    int tid = threadIdx.x; int bid_M = blockIdx.x; int bid_N = blockIdx.y; int bid_P = blockIdx.z;
    auto gX_slab = make_tensor(make_gmem_ptr(a_ptr), mos.X.gSlab);
    auto gB_slab = make_tensor(make_gmem_ptr(B_ptr), mos.B.gSlab);
    auto gC_slab = make_tensor(make_gmem_ptr(C_ptr), mos.C.gSlab);
    auto gX_batch = slice_rest(gX_slab, mos.X.BatchBlock, make_coord(bid_M, bid_P));
    typename Mosaic::SympowCoords c{};
    constexpr static int smempipe = mos.perf.smempipe > c.num_elements ? c.num_elements : mos.perf.smempipe;
    extern __shared__ char smem[];
    Allocator<16> alloc(smem);
    AT* X_smem = alloc.allocate<AT>(int(size(mos.X.sBatch)) * smempipe);
    BT* B_smem = alloc.allocate<BT>(size(mos.B.sTile) * smempipe);
    auto pipe = SmemPipe<smempipe>();
    auto sX_batch = make_tensor(make_smem_ptr(X_smem), mos.X.sBatch);
    auto sB_tile_pipe = pipe.create(B_smem, mos.B.sTile, mos.B.tile_copy);
    if (tid < size<1>(mos.X.batch_copy.FrgThr))
        copy(mos.X.batch_copy.g2s_atom,
            slice_rest(gX_batch, mos.X.batch_copy.FrgThr, tid),
            slice_rest(sX_batch, mos.X.batch_copy.FrgThr, tid));
    cp_async_fence(); cp_async_wait<0>(); __syncthreads();
    auto rA_frg_mma = make_tensor<typename Mosaic::FrgTypeA>(mos.A.mma_Frg);
    auto rB_frg_mma = make_tensor<typename Mosaic::FrgTypeB>(mos.B.mma_Frg);
    auto rC_frg_mma = make_tensor<typename Mosaic::FrgTypeC>(mos.C.mma_Frg);
    clear(rC_frg_mma);
    auto rXi_tprod_frg = make_tuple(make_tensor<AT>(get<Is>(mos.Xi).Frg)...);
    auto rY_tprod_frg = rA_frg_mma.compose(mos.Y_tprod_frg__2__A_mma_frg);
    // prefill
    auto pipe_fetch = [&](int k_tile) {
        if (k_tile < c.num_elements) {
            auto gB_tile = slice_rest(gB_slab, mos.B.TileBlock, make_coord(bid_N, k_tile, bid_P));
            pipe.fetch(gB_tile, sB_tile_pipe, mos.B.tile_copy);
        }
        pipe.commit();
    };
    for (int k_tile = 0; k_tile < smempipe - 1; ++k_tile) {
        pipe_fetch(k_tile);
        pipe.step();
    }
    // main loop
    for (; c.idx < c.num_elements; ++c) {
        pipe_fetch(c.idx + smempipe - 1);
        pipe.ready();
        auto sB_tile = pipe.read(sB_tile_pipe);
        if constexpr (mos.perf.regpipe == 0)
            load_frg<BT, mos.perf.use_ldsm, sizeof(BT) == 2>(sB_tile, mos.B.mma_FrgThr, rB_frg_mma);
        auto X_block_coords = make_coord(c.seq, _0{});
        auto sXi_tile = make_tuple(slice_rest(sX_batch, get<Is>(mos.Xi).TileBlock, X_block_coords)...);
        (..., (load_frg<AT, mos.perf.use_ldsm, false>(get<Is>(sXi_tile), get<Is>(mos.Xi).tprod_FrgThr, get<Is>(rXi_tprod_frg))));
        tprod(rY_tprod_frg, get<Is>(rXi_tprod_frg)...);
        if constexpr (duplicate_correction)
            tensor_scalar_prod(rY_tprod_frg, static_cast<typename Mosaic::FrgTypeA>(sqrtf(c.duplicate_count())));
        mosaic::gemm(mos, rA_frg_mma, rB_frg_mma, sB_tile, rC_frg_mma);
        pipe.step();
    }
    pipe.finish();
    // write back
    alloc.reset(smem);
    CT* C_smem = alloc.allocate<CT>(int(size(mos.C.sTile)));
    auto sC_tile = make_tensor(make_smem_ptr(C_smem), mos.C.sTile);
    copy(rC_frg_mma, slice_rest(sC_tile, mos.C.mma_FrgThr, tid));
    __syncthreads();
    auto gC_tile = slice_rest(gC_slab, mos.C.TileBlock, make_coord(bid_M, bid_N, bid_P));
    if (tid < size<1>(mos.C.tile_copy.FrgThr))
        copy(mos.C.tile_copy.universal_atom,
            slice_rest(sC_tile, mos.C.tile_copy.FrgThr, tid),
            slice_rest(gC_tile, mos.C.tile_copy.FrgThr, tid));
}


template <bool duplicate_correction, typename Mosaic, typename AT, typename BT, typename CT>
__global__ void sympow_K_mma_kernel(Mosaic mos, AT* a_ptr, BT* B_ptr, CT* C_ptr) {
    sympow_K_mma_kernel_impl<duplicate_correction>(make_int_sequence<mos.pow>{}, mos, a_ptr, B_ptr, C_ptr);
}


template<bool duplicate_correction=true, int smempipe=1, typename Mosaic, typename AT, typename BT, typename CT>
void launch_sympow_mma_kernel(Mosaic mos, AT* a_ptr, BT* B_ptr, CT* C_ptr) {
    dim3 blocks(size<0>(mos.C.Blocks), size<1>(mos.C.Blocks), size<2>(mos.C.Blocks));
    int threads = Mosaic::thread_num;
    int smem_size = mos.smem_size();
    if constexpr (mos.expand_K) {
        auto kernel = sympow_K_mma_kernel<duplicate_correction, Mosaic, AT, BT, CT>;
        adjust_dynamic_smem_size(kernel, smem_size);
        kernel<<<blocks,threads,smem_size>>>(mos, a_ptr, B_ptr, C_ptr);
    } else {
        auto kernel = sympow_M_mma_kernel<duplicate_correction, Mosaic, AT, BT, CT>;
        adjust_dynamic_smem_size(kernel, smem_size);
        kernel<<<blocks,threads,smem_size>>>(mos, a_ptr, B_ptr, C_ptr);
    }

    // Check for kernel launch failure
    cudaError_t err = cudaGetLastError();
    if (err != cudaSuccess) {
        fprintf(stderr, "CUDA kernel launch error: %s\n", cudaGetErrorString(err));
        throw std::runtime_error(cudaGetErrorString(err));
    }
}

} // namespace mosaic