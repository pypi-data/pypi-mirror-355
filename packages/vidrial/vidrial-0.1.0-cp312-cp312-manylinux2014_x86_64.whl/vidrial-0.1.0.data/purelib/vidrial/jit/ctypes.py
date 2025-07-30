# credit: 
import copy
import ctypes
import torch
from typing import Any, Dict, Iterable, Tuple


# Type map from torch dtype to cutlass dtype
dtype_map = {
    torch.float16: 'cutlass::half_t',
    torch.float32: 'float',
    torch.float64: 'double',
    torch.bfloat16: 'cutlass::bfloat16_t',
}

# Name map for Python `eval`
typename_map: Dict[Any, str] = {
    **{t: t.__name__ for t in (bool, int, float)},
    torch.int: 'torch.int',
    torch.float: 'torch.float',
    torch.float16: 'torch.float16',
    torch.bfloat16: 'torch.bfloat16',
    torch.float32: 'torch.float32',
    torch.float64: 'torch.float64',
    torch.float8_e4m3fn: 'torch.float8_e4m3fn',
    torch.cuda.Stream: 'torch.cuda.Stream',
}

# `ctype` map for Python casting
ctype_map: Dict[Any, Any] = {
    **{t: getattr(ctypes, f'c_{t.__name__}') for t in (bool, int, float)},
    **{t: ctypes.c_void_p for t in (torch.int, torch.float, torch.float32, torch.float64, torch.bfloat16, torch.float8_e4m3fn, torch.cuda.Stream)},
}

# Type map for both Python API and source code usages
genc_map = {
    bool: ('bool', 'bool'),
    int: ('int', 'int'),
    float: ('float', 'float'),
    torch.int: ('void*', 'int*'),
    torch.float: ('void*', 'float*'),
    torch.float32: ('void*', 'float*'),
    torch.float64: ('void*', 'double*'),
    torch.float16: ('void*', 'cutlass::half_t*'),
    torch.bfloat16: ('void*', 'cutlass::bfloat16_t*'),
    torch.float8_e4m3fn: ('void*', 'cutlass::float_e4m3_t*'),
    torch.cuda.Stream: ('void*', 'cudaStream_t'),
}

def map_ctype(value: Any) -> Any:
    if hasattr(value, 'data_ptr'):
        if value.dtype == torch.int:
            return ctypes.c_void_p(value.data_ptr())
        elif value.dtype == torch.float:
            return ctypes.c_void_p(value.data_ptr())
        elif value.dtype == torch.float32:
            return ctypes.c_void_p(value.data_ptr())
        elif value.dtype == torch.float64:
            return ctypes.c_void_p(value.data_ptr())
        elif value.dtype == torch.bfloat16:
            return ctypes.c_void_p(value.data_ptr())
        elif value.dtype == torch.float16:
            return ctypes.c_void_p(value.data_ptr())
        elif value.dtype == torch.float8_e4m3fn:
            return ctypes.c_void_p(value.data_ptr())
        else:
            return ctypes.c_void_p(value.data_ptr())

    if hasattr(value, 'cuda_stream'):
        return ctypes.c_void_p(value.cuda_stream)

    if isinstance(value, bool):
        return ctypes.c_bool(value)
    elif isinstance(value, int):
        return ctypes.c_int(value)
    elif isinstance(value, float):
        return ctypes.c_float(value)

    return ctype_map[type(value)](value)
