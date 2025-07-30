#include "../copy/copy_kernels.cuh"
using namespace cute;
using namespace mosaic;

template<typename T, int thread_num, typename SlabShape, typename TileShape, typename GSlab>
void launch_add_one_inplace(T* ptr) {
    auto mosaic = make_tiling_mosaic<T, thread_num>(SlabShape{}, TileShape{}, GSlab{});
    auto gA = make_tensor(ptr, GSlab{});
    int blocks = size<1>(mosaic.TileBlock);
    tensor_scalar_add_kernel<<<blocks, int(mosaic.thread_num)>>>(mosaic, gA.data(), gA.data(), 1.f);
}

template<typename T, int thread_num, typename SlabShape, typename TileShape, typename GSlab>
void launch_add_one(T* in, T* out) {
    auto mosaic = make_tiling_mosaic<T, thread_num>(SlabShape{}, TileShape{}, GSlab{});
    auto gA = make_tensor(in, GSlab{});
    auto gB = make_tensor(out, GSlab{});
    int blocks = size<1>(mosaic.TileBlock);
    tensor_scalar_add_kernel<<<blocks, int(mosaic.thread_num)>>>(mosaic, gA.data(), gB.data(), 1.f);
}
