#pragma once

#include <cuda_runtime.h>
#include <iostream>

namespace mosaic {

template <typename Kernel>
void adjust_dynamic_smem_size(Kernel& kernel, int smem_size) {
    if (smem_size > 48 * 1024) {
        auto err = cudaFuncSetAttribute(
            kernel, cudaFuncAttributeMaxDynamicSharedMemorySize, smem_size);
        if (err != cudaSuccess) {
            std::cerr << "Error setting max dynamic shared memory size: " << cudaGetErrorString(err) << std::endl;
        }
    }
}

} // namespace mosaic