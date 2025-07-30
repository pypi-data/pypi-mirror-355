import torch
import pytest
from vidrial.jit.ctypes import dtype_map
from vidrial.jit.jit import jit

@pytest.fixture
def get_add_one_kernel_code():
    def _get_add_one_kernel_code(input: torch.Tensor, output: torch.Tensor, tile_d0: int = 32, tile_d1: int = 32, thread_num: int = 32):
        d0, d1 = input.shape
        assert input.dtype == output.dtype, f"Input and output must have the same dtype, got {input.dtype} and {output.dtype}"
        return """
#include "add_one/add_one_kernels.cuh"
#include "copy/copy_kernels.cuh"
using namespace cute;
using namespace mosaic;

extern "C" {{
    void launch(float* In, float* Out) {{
        using SlabShape = Shape<Int<{d0}>, Int<{d1}>>;
        using TileShape = Shape<Int<{tile_d0}>, Int<{tile_d1}>>;
        using ASlab = Layout<SlabShape>;
        using T = {T};
        //T* in_ptr = reinterpret_cast<T*>(In);
        //T* out_ptr = reinterpret_cast<T*>(Out);
        launch_add_one<float, {thread_num}, SlabShape, TileShape, ASlab>(In, Out);
    }}
}}
        """.format(d0=d0, d1=d1, tile_d0=tile_d0, tile_d1=tile_d1, thread_num=thread_num, T=dtype_map[input.dtype])
    return _get_add_one_kernel_code


@pytest.fixture
def add_one_kernel(get_add_one_kernel_code, tmp_path):
    def _add_one_kernel(X, Y, d0_tile, d1_tile, thread_num):
        code = get_add_one_kernel_code(X, Y, d0_tile, d1_tile, thread_num)
        runtime = jit("test_add_one_kernel", code, root=str(tmp_path))
        runtime(X, Y)
        return Y
    return _add_one_kernel