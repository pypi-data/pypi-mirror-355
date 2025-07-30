# Query the GPU properties of the current machine
# This file is inspired by https://gist.github.com/f0k/63a664160d016a491b2cbea15913d549
import logging
import ctypes
from functools import partial
from enum import Enum
from typing import Any
logger = logging.getLogger(__name__)

CUDA_SUCCESS = 0

# Constants taken from cuda.h
class CUDA_DEVICE_ATTRIBUTE(Enum):
    CU_DEVICE_ATTRIBUTE_MAX_THREADS_PER_BLOCK = 1                          # Maximum number of threads per block 
    CU_DEVICE_ATTRIBUTE_MAX_BLOCK_DIM_X = 2                                # Maximum block dimension X 
    CU_DEVICE_ATTRIBUTE_MAX_BLOCK_DIM_Y = 3                                # Maximum block dimension Y 
    CU_DEVICE_ATTRIBUTE_MAX_BLOCK_DIM_Z = 4                                # Maximum block dimension Z 
    CU_DEVICE_ATTRIBUTE_MAX_GRID_DIM_X = 5                                 # Maximum grid dimension X 
    CU_DEVICE_ATTRIBUTE_MAX_GRID_DIM_Y = 6                                 # Maximum grid dimension Y 
    CU_DEVICE_ATTRIBUTE_MAX_GRID_DIM_Z = 7                                 # Maximum grid dimension Z 
    CU_DEVICE_ATTRIBUTE_MAX_SHARED_MEMORY_PER_BLOCK = 8                    # Maximum shared memory available per block in bytes 
    CU_DEVICE_ATTRIBUTE_TOTAL_CONSTANT_MEMORY = 9                          # Memory available on device for __constant__ variables in a CUDA C kernel in bytes 
    CU_DEVICE_ATTRIBUTE_WARP_SIZE = 10                                     # Warp size in threads 
    CU_DEVICE_ATTRIBUTE_MAX_PITCH = 11                                     # Maximum pitch in bytes allowed by memory copies 
    CU_DEVICE_ATTRIBUTE_MAX_REGISTERS_PER_BLOCK = 12                       # Maximum number of 32-bit registers available per block 
    CU_DEVICE_ATTRIBUTE_CLOCK_RATE = 13                                    # Typical clock frequency in kilohertz 
    CU_DEVICE_ATTRIBUTE_TEXTURE_ALIGNMENT = 14                             # Alignment requirement for textures 
    CU_DEVICE_ATTRIBUTE_MULTIPROCESSOR_COUNT = 16                          # Number of multiprocessors on device 
    CU_DEVICE_ATTRIBUTE_KERNEL_EXEC_TIMEOUT = 17                           # Specifies whether there is a run time limit on kernels 
    CU_DEVICE_ATTRIBUTE_INTEGRATED = 18                                    # Device is integrated with host memory 
    CU_DEVICE_ATTRIBUTE_CAN_MAP_HOST_MEMORY = 19                           # Device can map host memory into CUDA address space 
    CU_DEVICE_ATTRIBUTE_COMPUTE_MODE = 20                                  # Compute mode (See ::CUcomputemode for details) 
    CU_DEVICE_ATTRIBUTE_CONCURRENT_KERNELS = 31                            # Device can possibly execute multiple kernels concurrently 
    CU_DEVICE_ATTRIBUTE_ECC_ENABLED = 32                                   # Device has ECC support enabled 
    CU_DEVICE_ATTRIBUTE_MEMORY_CLOCK_RATE = 36                             # Peak memory clock frequency in kilohertz 
    CU_DEVICE_ATTRIBUTE_GLOBAL_MEMORY_BUS_WIDTH = 37                       # Global memory bus width in bits 
    CU_DEVICE_ATTRIBUTE_L2_CACHE_SIZE = 38                                 # Size of L2 cache in bytes 
    CU_DEVICE_ATTRIBUTE_MAX_THREADS_PER_MULTIPROCESSOR = 39                # Maximum resident threads per multiprocessor 
    CU_DEVICE_ATTRIBUTE_UNIFIED_ADDRESSING = 41                            # Device shares a unified address space with the host 
    CU_DEVICE_ATTRIBUTE_COMPUTE_CAPABILITY_MAJOR = 75                      # Major compute capability version number 
    CU_DEVICE_ATTRIBUTE_COMPUTE_CAPABILITY_MINOR = 76                      # Minor compute capability version number 
    CU_DEVICE_ATTRIBUTE_STREAM_PRIORITIES_SUPPORTED = 78                   # Device supports stream priorities 
    CU_DEVICE_ATTRIBUTE_GLOBAL_L1_CACHE_SUPPORTED = 79                     # Device supports caching globals in L1 
    CU_DEVICE_ATTRIBUTE_LOCAL_L1_CACHE_SUPPORTED = 80                      # Device supports caching locals in L1 
    CU_DEVICE_ATTRIBUTE_MAX_SHARED_MEMORY_PER_MULTIPROCESSOR = 81          # Maximum shared memory available per multiprocessor in bytes 
    CU_DEVICE_ATTRIBUTE_MAX_REGISTERS_PER_MULTIPROCESSOR = 82              # Maximum number of 32-bit registers available per multiprocessor 
    CU_DEVICE_ATTRIBUTE_MANAGED_MEMORY = 83                                # Device can allocate managed memory on this system 
    CU_DEVICE_ATTRIBUTE_MULTI_GPU_BOARD = 84                               # Device is on a multi-GPU board 
    CU_DEVICE_ATTRIBUTE_MULTI_GPU_BOARD_GROUP_ID = 85                      # Unique id for a group of devices on the same multi-GPU board 
    CU_DEVICE_ATTRIBUTE_SINGLE_TO_DOUBLE_PRECISION_PERF_RATIO = 87         # Ratio of single precision performance (in floating-point operations per second) to double precision performance 
    CU_DEVICE_ATTRIBUTE_CONCURRENT_MANAGED_ACCESS = 89                     # Device can coherently access managed memory concurrently with the CPU 
    CU_DEVICE_ATTRIBUTE_CAN_USE_HOST_POINTER_FOR_REGISTERED_MEM = 91       # Device can access host registered memory at the same virtual address as the CPU 
    CU_DEVICE_ATTRIBUTE_COOPERATIVE_LAUNCH = 95                            # Device supports launching cooperative kernels via ::cuLaunchCooperativeKernel 
    CU_DEVICE_ATTRIBUTE_MAX_SHARED_MEMORY_PER_BLOCK_OPTIN = 97             # Maximum optin shared memory per block 
    CU_DEVICE_ATTRIBUTE_MAX_BLOCKS_PER_MULTIPROCESSOR = 106                # Maximum number of blocks per multiprocessor 
    CU_DEVICE_ATTRIBUTE_MAX_PERSISTING_L2_CACHE_SIZE = 108                 # Maximum L2 persisting lines capacity setting in bytes. 
    CU_DEVICE_ATTRIBUTE_RESERVED_SHARED_MEMORY_PER_BLOCK = 111             # Shared memory reserved by CUDA driver per block in bytes 
    CU_DEVICE_ATTRIBUTE_TENSOR_MAP_ACCESS_SUPPORTED = 127                  # Device supports accessing memory using Tensor Map. 


def ConvertSMVer2Cores(major, minor):
    # Returns the number of CUDA cores per multiprocessor for a given
    # Compute Capability version. There is no way to retrieve that via
    # the API, so it needs to be hard-coded.
    # See _ConvertSMVer2Cores in helper_cuda.h in NVIDIA's CUDA Samples.
    return {(1, 0): 8,    # Tesla
            (1, 1): 8,
            (1, 2): 8,
            (1, 3): 8,
            (2, 0): 32,   # Fermi
            (2, 1): 48,
            (3, 0): 192,  # Kepler
            (3, 2): 192,
            (3, 5): 192,
            (3, 7): 192,
            (5, 0): 128,  # Maxwell
            (5, 2): 128,
            (5, 3): 128,
            (6, 0): 64,   # Pascal
            (6, 1): 128,
            (6, 2): 128,
            (7, 0): 64,   # Volta
            (7, 2): 64,
            (7, 5): 64,   # Turing
            (8, 0): 64,   # Ampere
            (8, 6): 128,
            (8, 7): 128,
            (8, 9): 128,  # Ada
            (9, 0): 128,  # Hopper
            }.get((major, minor), 0)


def get_cuda_device_properties(attrs) -> list[dict[str, Any]]:
    libnames = ('libcuda.so', 'libcuda.dylib', 'nvcuda.dll', 'cuda.dll')
    for libname in libnames:
        try:
            cuda = ctypes.CDLL(libname)
        except OSError:
            continue
        else:
            break
    else:
        raise OSError("could not load any of: " + ' '.join(libnames))

    nGpus = ctypes.c_int()
    name = b' ' * 100
    cc_major = ctypes.c_int()
    cc_minor = ctypes.c_int()
    threads_per_core = ctypes.c_int()
    freeMem = ctypes.c_size_t()
    totalMem = ctypes.c_size_t()

    result = ctypes.c_int()
    device = ctypes.c_int()
    context = ctypes.c_void_p()
    error_str = ctypes.c_char_p()

    result = cuda.cuInit(0)
    if result != CUDA_SUCCESS:
        cuda.cuGetErrorString(result, ctypes.byref(error_str))
        logger.error("cuInit failed with error code %d: %s" % (result, error_str.value.decode()))
        return 1
    result = cuda.cuDeviceGetCount(ctypes.byref(nGpus))
    if result != CUDA_SUCCESS:
        cuda.cuGetErrorString(result, ctypes.byref(error_str))
        logger.error("cuDeviceGetCount failed with error code %d: %s" % (result, error_str.value.decode()))
        return 1
    logger.info("Found %d device(s)." % nGpus.value)
    res = [{} for _ in range(int(nGpus.value))]
    for i in range(nGpus.value):
        result = cuda.cuDeviceGet(ctypes.byref(device), i)
        if result != CUDA_SUCCESS:
            cuda.cuGetErrorString(result, ctypes.byref(error_str))
            logger.error("cuDeviceGet failed with error code %d: %s" % (result, error_str.value.decode()))
            return 1
        logger.info("Device: %d" % i)
        if cuda.cuDeviceGetName(ctypes.c_char_p(name), len(name), device) == CUDA_SUCCESS:
            res[i]['name'] = name.split(b'\0', 1)[0].decode()
        if cuda.cuDeviceComputeCapability(ctypes.byref(cc_major), ctypes.byref(cc_minor), device) == CUDA_SUCCESS:
            res[i]['compute_capability'] = (cc_major.value, cc_minor.value)
        for attr in attrs:
            v = ctypes.c_int()
            if cuda.cuDeviceGetAttribute(ctypes.byref(v), attr.value, device) == CUDA_SUCCESS:    
                res[i][attr.name] = v.value
                if attr == CUDA_DEVICE_ATTRIBUTE.CU_DEVICE_ATTRIBUTE_MULTIPROCESSOR_COUNT:
                    res[i]['cuda_cores'] = v.value * ConvertSMVer2Cores(cc_major.value, cc_minor.value)
                    if cuda.cuDeviceGetAttribute(ctypes.byref(threads_per_core), CUDA_DEVICE_ATTRIBUTE.CU_DEVICE_ATTRIBUTE_MAX_THREADS_PER_MULTIPROCESSOR.value, device) == CUDA_SUCCESS:
                        res[i]['cuda_threads'] = v.value * threads_per_core.value
                if attr == CUDA_DEVICE_ATTRIBUTE.CU_DEVICE_ATTRIBUTE_CLOCK_RATE:
                    res[i]['clock_rate (MHz)'] = v.value / 1000.
                if attr == CUDA_DEVICE_ATTRIBUTE.CU_DEVICE_ATTRIBUTE_MEMORY_CLOCK_RATE:
                    res[i]['memory_clock_rate (MHz)'] = v.value / 1000.


        try:
            result = cuda.cuCtxCreate_v2(ctypes.byref(context), 0, device)
        except AttributeError:
            result = cuda.cuCtxCreate(ctypes.byref(context), 0, device)
        if result != CUDA_SUCCESS:
            cuda.cuGetErrorString(result, ctypes.byref(error_str))
            logger.error("cuCtxCreate failed with error code %d: %s" % (result, error_str.value.decode()))
        else:
            try:
                result = cuda.cuMemGetInfo_v2(ctypes.byref(freeMem), ctypes.byref(totalMem))
            except AttributeError:
                result = cuda.cuMemGetInfo(ctypes.byref(freeMem), ctypes.byref(totalMem))
            if result == CUDA_SUCCESS:
                res[i]['total_memory (MiB)'] = totalMem.value / 1024**2
                res[i]['free_memory (MiB)'] = freeMem.value / 1024**2
            else:
                cuda.cuGetErrorString(result, ctypes.byref(error_str))
                logger.error("cuMemGetInfo failed with error code %d: %s" % (result, error_str.value.decode()))
            cuda.cuCtxDetach(context)
    return res


get_cuda_device_basic_props = partial(get_cuda_device_properties, [
    CUDA_DEVICE_ATTRIBUTE.CU_DEVICE_ATTRIBUTE_MULTIPROCESSOR_COUNT,
    CUDA_DEVICE_ATTRIBUTE.CU_DEVICE_ATTRIBUTE_MAX_THREADS_PER_MULTIPROCESSOR,
    CUDA_DEVICE_ATTRIBUTE.CU_DEVICE_ATTRIBUTE_CLOCK_RATE,
    CUDA_DEVICE_ATTRIBUTE.CU_DEVICE_ATTRIBUTE_MEMORY_CLOCK_RATE,
    CUDA_DEVICE_ATTRIBUTE.CU_DEVICE_ATTRIBUTE_MAX_SHARED_MEMORY_PER_MULTIPROCESSOR,
    CUDA_DEVICE_ATTRIBUTE.CU_DEVICE_ATTRIBUTE_MAX_REGISTERS_PER_MULTIPROCESSOR,
])
