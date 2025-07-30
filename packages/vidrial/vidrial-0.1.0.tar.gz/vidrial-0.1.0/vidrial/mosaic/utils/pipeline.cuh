#pragma once
#include "copy_mosaic.cuh"

#define CUDA_CHECK(expr) \
    do { \
        cudaError_t err = (expr); \
        if (err != cudaSuccess) { \
            fprintf(stderr, "CUDA error: %s\n", cudaGetErrorString(err)); \
            throw std::runtime_error(cudaGetErrorString(err)); \
        } \
    } while(0)

namespace mosaic {


/**
 * A smem pipeline object deals with the prefetching of smem tiles.
 * 
 * A pipeline object has a "stage" attribute that tracks the number of
 * steps that a pipeline has taken. There're 2 types of ways for a pipeline
 * to take a step:
 * 
 *  1. prefill: Keep fetching tiles without reading them
 *      fetch() -> commit() -> step()
 *  2. fetch & read: Fetch tiles and read them along the way
 *      fetch() -> commit() -> ready() -> read() -> step()
 * 
 *  fetch(): prefetch a tile from a tensorpipe into the pipeline
 *  commit(): commit all previous fetches
 *  ready(): wait for the pipeline to be ready for consumption
 *  read(): read the pipeline
 *  step(): take a step in the pipeline
 * 
 *  A pipeline keeps track of the number of steps it has taken in the "stage"
 *  attribute, and the following semantic is applied:
 *  
 *  1. fetch() always writes to region pointed by "stage % Depth"
 *  2. read() always reads from the region pointed by "(stage + 1) % Depth"
 * 
 * 
 */

template<int Depth> 
struct SmemPipe {
    static_assert(Depth > 0, "Depth must be greater than 0");
    int stage;

    CUTE_DEVICE SmemPipe(): stage(0) {}

    /*
     * Create a tensor pipe based on the smem pointer and the copy mosaics
     */
    template<typename STile, typename CopyMosaic, typename offset_t>
    CUTE_DEVICE auto create(void* smem_ptr, STile const& sTile, CopyMosaic const& mosaic, offset_t const offset) {
        using T = CopyMosaic::T;
        using STilePipe = decltype(tiled_product(STile{}, Int<Depth>{}));
        auto pipe = make_tensor(make_smem_ptr(reinterpret_cast<T*>(smem_ptr) + offset), STilePipe{});
        return pipe;
    }

    template<typename STile, typename CopyMosaic>
    CUTE_DEVICE auto create(void* smem_ptr, STile const& sTile, CopyMosaic const& mosaic) {
        return create(smem_ptr, sTile, mosaic, size_t(0));
    }

    /*
     * Load from a global memory tile into a smem tile pointed by stage
     */
    template<typename GTile, typename TensorPipe, typename CopyMosaic>
    CUTE_DEVICE void fetch(GTile const& g_tile, TensorPipe const& tensor_pipe, CopyMosaic const& mos) {
        const int tid = threadIdx.x;
        int dst_depth = int(stage) % Depth;
        auto dst_tile = slice_rest(tensor_pipe, dst_depth);
        auto& g2s_atom = mos.g2s_atom;
        auto g_frag = slice_rest(g_tile, mos.FrgThr, tid);
        auto s_frag = slice_rest(dst_tile, mos.FrgThr, tid);
        CUTE_STATIC_ASSERT_V(shape(g_tile) == shape(dst_tile), "Tile size mismatch");

        if (tid < size<1>(mos.FrgThr))
            copy(g2s_atom, g_frag, s_frag);
    }

    /*
     * Take a step in the pipeline
     */
    CUTE_DEVICE void step() {
        stage++;
        // TODO(sean): check if this affects performance
        if constexpr (Depth <= 2)
            __syncthreads();
    }

    /*
     * Commit all previous fetches
     */
    CUTE_DEVICE void commit() {
        cp_async_fence();
    }

    /* 
     * Wait for the current read stage to be ready for consumption
     */
    CUTE_DEVICE void ready() {
        cute::cp_async_wait<Depth - 1>();
        __syncthreads();
    }

    /*
     * Return the current stage from the tensor pipe
     */
    template<typename TensorPipe>
    CUTE_DEVICE auto read(TensorPipe const& tensor_pipe) {
        return slice_rest(tensor_pipe, (stage + 1) % Depth);
    }


    /*
     * Clear up artificial barriers placed by the pipeline
     */
    CUTE_DEVICE void finish() {
        cute::cp_async_wait<0>();
    }

};
}