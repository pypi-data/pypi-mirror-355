#pragma once
#include "../../mosaic/mosaics/mma_mosaic.cuh"
#include "../../mosaic/utils/copy.cuh"
#include "../../mosaic/utils/gemm.cuh"
#include "../../mosaic/utils/pipeline.cuh"
#include "../../mosaic/utils/launch.cuh"
#include "../../mosaic/utils/allocator.cuh"
namespace mosaic {

template <typename Mosaic, typename T>
__global__ void tiled_mma_kernel(Mosaic mos, T* A_ptr, T* B_ptr, T* C_ptr) {
    int tid = threadIdx.x;
    int bid_M = blockIdx.x; int bid_N = blockIdx.y; int bid_P = blockIdx.z;
    auto tile_coords = MmaMNKCoords(mos.MNK_tile_shape);
    tile_coords.step_M(blockIdx.x); tile_coords.step_N(blockIdx.y); tile_coords.step_P(blockIdx.z);
    // ----- Global memory slabs -----
    auto gA_slab = make_tensor(make_gmem_ptr(A_ptr), mos.A.gSlab);
    auto gB_slab = make_tensor(make_gmem_ptr(B_ptr), mos.B.gSlab);
    auto gC_slab = make_tensor(make_gmem_ptr(C_ptr), mos.C.gSlab);
    // ----- Shared memory pipelines -----
    constexpr static int smempipe = static_min(mos.perf.smempipe, mos.K_tile_num);
    auto pipe = SmemPipe<smempipe>();
    extern __shared__ char smem[];
    Allocator<16> alloc(smem);
    T* A_smem = alloc.allocate<T>(size(mos.A.sTile) * smempipe);
    T* B_smem = alloc.allocate<T>(size(mos.B.sTile) * smempipe);
    auto sA_tile_pipe = pipe.create(A_smem, mos.A.sTile, mos.A.tile_copy);
    auto sB_tile_pipe = pipe.create(B_smem, mos.B.sTile, mos.B.tile_copy);
    auto rA_frg_mma = mos.A.make_mma_frg();
    auto rB_frg_mma = mos.B.make_mma_frg();
    auto rC_frg_mma = mos.C.make_mma_frg();
    clear(rC_frg_mma);
    // ----- Pipeline fetch A_tile and B_tile -----
    auto pipe_fetch = [&]() {
        if (tile_coords.valid_K_tile(mos.K)) {
            auto gA_tile = tile_coords.slice_A_tile(gA_slab);
            auto gB_tile = tile_coords.slice_B_tile(gB_slab);
            pipe.fetch(gA_tile, sA_tile_pipe, mos.A.tile_copy);
            pipe.fetch(gB_tile, sB_tile_pipe, mos.B.tile_copy);
            tile_coords.step_K();
        }
        pipe.commit();
    };
    // ----- Prefill pipeline -----
    for (; pipe.stage < smempipe - 1; pipe.step())
        pipe_fetch();
    // ----- Main loop -----
    for (int k_tile = 0; k_tile < mos.K_tile_num; k_tile++) {
        pipe_fetch();
        pipe.ready();
        auto sA_tile = pipe.read(sA_tile_pipe);
        auto sB_tile = pipe.read(sB_tile_pipe);
        load_frg<T, mos.perf.use_ldsm, false>(sA_tile, mos.A.mma_FrgThr, rA_frg_mma);
        if constexpr (mos.perf.regpipe == 0)
            load_frg<T, mos.perf.use_ldsm, false>(sB_tile, mos.B.mma_FrgThr, rB_frg_mma);
        mosaic::gemm(mos, rA_frg_mma, rB_frg_mma, sB_tile, rC_frg_mma);
        pipe.step();
    }
    pipe.finish();
    // ----- Write C_tile to global memory -----
    alloc.reset(smem);
    T* C_smem = alloc.allocate<T>(size(mos.C.sTile));
    auto sC_tile = make_tensor(make_smem_ptr(C_smem), mos.C.sTile);
    copy(rC_frg_mma, slice_rest(sC_tile, mos.C.mma_FrgThr, tid));
    __syncthreads();
    auto gC_tile = tile_coords.slice_C_tile(gC_slab);
    CTA_copy_tile(mos.C.tile_copy, sC_tile, gC_tile);
}

void launch_tiled_mma_kernel(auto mos, auto A_ptr, auto B_ptr, auto C_ptr) {
    dim3 blocks(mos.M_blocks, mos.N_blocks, mos.P_blocks);
    int threads = int(size(mos.Threads));
    using T = typename decltype(mos)::T;
    int smem_size = mos.smem_size();
    auto kernel = tiled_mma_kernel<decltype(mos), T>;
    adjust_dynamic_smem_size(kernel, smem_size);
    kernel<<<blocks, threads, smem_size>>>(mos, A_ptr, B_ptr, C_ptr);
}

} // namespace mosaic
