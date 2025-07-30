#pragma once

/*
 * A share memory allocator for CUDA kernels that respects alignment
 * 
 * Usage:
 * Example 1 - always allocate 16-byte aligned memory
 *   extern __shared__ char smem[];
 *   int n = 100;
 *   Allocator<16> alloc(smem);
 *   float* ptr = alloc.allocate<float>(n);
 * 
 * Example 2 - default align to 16 byte, but allocate 128-byte aligned memory
 *   extern __shared__ char smem[];
 *   int n = 100;
 *   Allocator<16> alloc(smem);
 *   float* ptr = alloc.allocate<128, float>(n);
 * 
 * Example 3 - compute the total share memory required upfront
 *   int a = 100, b = 200, c = 300;
 *   int total_size = Allocator<16>::total<half_t, half_t, float>(a, b, c);
 */
template <int default_alignment_=16>
struct Allocator {
    constexpr static int default_alignment = default_alignment_;
    using index_t = uint64_t;
private:
    int8_t* ptr_;

    template <int alignment>
    CUTE_HOST_DEVICE void aligns() {
        if constexpr (alignment > 0) {
            index_t addr = reinterpret_cast<index_t>(ptr_);
            if (addr % alignment != 0) {
                ptr_ = reinterpret_cast<int8_t*>(addr + alignment - addr % alignment);
            }
        }
    }

public:
    /*
     * Constructor
     * @param ptr: pointer to the shared memory
     */
    template <typename T>
    CUTE_HOST_DEVICE Allocator(T* ptr) : ptr_(reinterpret_cast<int8_t*>(ptr)) {}

    /*
     * Allocate memory
     * @param n: number of elements to allocate
     * @param alignment: alignment of the memory
     * @return pointer to the allocated memory
     */
    template <typename T, int alignment>
    CUTE_HOST_DEVICE T* allocate(int n) {
        aligns<alignment>();
        auto ret = reinterpret_cast<T*>(ptr_);
        ptr_ += sizeof(T) * n;
        return ret;
    }

    /*
     * Allocate memory with default alignment
     * @param n: number of elements to allocate
     * @return pointer to the allocated memory
     */
    template <typename T>
    CUTE_HOST_DEVICE T* allocate(int n) {
        return allocate<T, default_alignment>(n);
    }

    /*
     * Reset the allocator
     * @param ptr: pointer to use for subsequent allocations
     */
    template <typename T>
    CUTE_HOST_DEVICE void reset(T* ptr) {
        ptr_ = reinterpret_cast<int8_t*>(ptr);
    }

    /*
     * Compute the total memory size required for a single type
     * @param n: number of elements to allocate
     * @return total memory size
     */
    template <typename T>
    CUTE_HOST_DEVICE static int total(int n) {
        return sizeof(T) * n;
    }
    
    /*
     * Compute the total memory size required for multiple types
     * @param n: number of elements to allocate
     * @param ns: number of elements to allocate for each type
     * @return total memory size
     */
    template <typename T, typename... Ts, typename... Args>
    CUTE_HOST_DEVICE static constexpr int total(int n, Args... ns) {
        int size = sizeof(T) * n;
        if constexpr (sizeof...(Ts) > 0) {
            int segment_size = (size + (size % default_alignment == 0 ? 0 : default_alignment - size % default_alignment));
                        
            // Recursively add sizes for remaining types
            return segment_size + total<Ts...>(ns...);
        } else {
            return size;
        }
    }
};