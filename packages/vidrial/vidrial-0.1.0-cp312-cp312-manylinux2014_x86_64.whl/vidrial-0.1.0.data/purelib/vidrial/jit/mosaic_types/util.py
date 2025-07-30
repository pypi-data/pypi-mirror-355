import torch
from typing import Any, Optional, Tuple
from vidrial.jit.mosaic_types.types import Layout, Shape, Stride, Int, Tuple
from vidrial.jit.mosaic_types.types import CudaDType

def nested_constructor(nested_dims):
    def f(seq, type, dim_spec):
        if isinstance(dim_spec, int):
            # Handle negative indices
            actual_dim = dim_spec if dim_spec >= 0 else len(seq) + dim_spec
            return type(Int(seq[actual_dim]))
        elif isinstance(dim_spec, (list, tuple)):
            # For nested dimensions, recursively build shape and stride for each
            return type(*[f(seq, type, nested_dim) for nested_dim in dim_spec])
        raise ValueError(f"Unsupported dimension specification: {dim_spec}")
    return lambda seq, type=Tuple: f(seq, type, nested_dims)

def layout_from_shape_stride(shape: tuple[int, ...], stride: tuple[int, ...], dims: Optional[tuple[Any, ...]] = None) -> Layout:
    dims = tuple(range(len(shape))) if dims is None else dims
    constructor = nested_constructor(dims)
    return Layout(constructor(shape, Shape), constructor(stride, Stride))

# Convinient layout constructors
def layout_from_tensor(t: torch.Tensor, dims: Optional[tuple[Any, ...]] = None) -> Layout:
    """ Create a layout from a tensor by specifying the layout from the dimensions of the 
    tensor. For example, for a tensor of shape (b, t, h, d), if we want to create a layout 
    with shape (d, (b, (t, h))), we can pass dims=(-1, (0, (1, 2))). The strides will be
    inferred correctly.

    Args:
        t: The tensor to create the layout from.
        dims: An ordered hierarchical tuple of dimensions to use for the layout.
    
    Returns:
        A Layout object with the specified shape and stride.
    """
    constructor = nested_constructor(dims)
    return Layout(constructor(t.shape, Shape), constructor(t.stride(), Stride))


def torch_dtype_to_c(dtype: torch.dtype) -> str:
    """Convert PyTorch dtype to C++ type string."""
    dtype_map = {
        torch.bfloat16: CudaDType.BFLOAT16.value,
        torch.float16: CudaDType.FLOAT16.value,
        torch.float32: CudaDType.FLOAT.value,
        torch.float64: CudaDType.DOUBLE.value,
        torch.int32: CudaDType.INT32.value,
        torch.int64: CudaDType.INT64.value,
        torch.uint8: CudaDType.UINT8.value,
    }
    if dtype not in dtype_map:
        raise ValueError(f"Unsupported dtype: {dtype}")
    return dtype_map[dtype]

NestedStructure = Tuple['NestedStructure', ...] | int

def test_layout_from_tensor():
    t = torch.randn(1, 2, 3, 4)
    layout = layout_from_tensor(t, (-1, (0, (1, 2))))
    assert layout.to_cpp() == "Layout<Shape<Int<4>, Shape<Int<1>, Shape<Int<2>, Int<3>>>>, Stride<Int<1>, Stride<Int<24>, Stride<Int<12>, Int<4>>>>>"
