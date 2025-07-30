import torch as th
import pytest
from vidrial.kernels.sympow.binding import binding, binding_autotuned
from vidrial.kernels.sympow.dimensions import sympow_dim, op_output_shape, interface_output_shape
from vidrial.jit.mosaic_types.types import Shape, Layout, Int
from vidrial.kernels.sympow.op import op, op_reference
from vidrial.mosaic.utils.common import diff
from vidrial.kernels.sympow.interface import interface
from vidrial.mosaic.utils.common import tpow_shape, tpow
from vidrial.mosaic.utils.test_utils import PERMUTATIONS_OF_STRIDES_UP_TO_4D, create_permuted_strides_layout

# Basic binding, op, and interface tests
def test_call_binding():
    b, d = 128, 64
    power, d_tile = 2, 8
    X = th.empty((b, d), device='cuda')
    Z = th.empty(op_output_shape(X.shape, power, d_tile), device='cuda')
    binding(Z, X, power, d_tile, duplicate_correction=True, b_tile=4,
            ZFrgShape=Shape(Shape(*[Int(2)]*power), Int(1)),
            SZTileLayout=Layout(Shape(Shape(*[Int(d_tile)]*power), Int(4))))
def test_sympow_op():
    b, d = 128, 64
    power, d_tile = 2, 8
    X = th.empty((b, d), device='cuda')
    Z = th.empty(op_output_shape(X.shape, power, d_tile), device='cuda')
    Z = op(X, power, d_tile, duplicate_correction=True)
    Z_ref = op_reference(X, power, d_tile, duplicate_correction=True)
    diff(Z, Z_ref, rtol=4e-2, atol=1e-2)
def test_sympow_interface():
    X = th.empty((8, 16), device='cuda')
    power, d_tile = 2, 8
    Z = interface(X, power, d_tile, dim=0)
    Z = interface(X, power, d_tile, dim=1)

# ----------- Shape Tests -----------
# TODO: move tpow tests somewhere else
@pytest.mark.parametrize("x_shape,expected,p", [
    ([2], [2,2], 2),
    ([3], [3,3], 2),
    ([5], [5,5], 2),
    ([9], [9,9], 2),
    ([2,4], [2,4,4], 2), # batch dims
    ([2,2], [2,2,2], 2),
    ([1,7,5], [1,7,5,5], 2),
    ([2,3,4,8], [2,3,4,8,8], 2),
    ([5], [5,5,5], 3),
    ([9], [9,9,9], 3),
])
def test_tpow_shape(x_shape, expected, p):
    assert tpow_shape(x_shape, p) == th.Size(expected)
    assert tpow_shape(th.Size(x_shape), p) == th.Size(expected)

@pytest.mark.parametrize("x_shape,expected,p", [
    ([2], [3], 2),
    ([3], [6], 2),
    ([4], [10], 2),
    ([5], [15], 2),
    ([7], [28], 2),
    ([8], [36], 2),
    ([9], [45], 2),
    ([10], [55], 2),
    ([2,4], [2,10], 2), # batch dims
    ([1,7,5], [1,7,15], 2),
    ([2,3,4,8], [2,3,4,36], 2),
])
def test_interface_output_shape(x_shape, expected, p):
    assert interface_output_shape(x_shape, p) == th.Size(expected)
    assert interface_output_shape(th.Size(x_shape), p) == th.Size(expected)


# # ----------- Kernel Tests -----------
SHAPES_AND_POWERS_AND_TILES = [
    ([2], 2, 1),
    ([4], 2, 2),
    ([3,8], 3, 4),
    ([3,2], 4, 1),
    ([2,3,8], 2, 1), # Multiple batch dims not implemented yet
    ([2,3,16], 3, 8), # Multiple batch dims not implemented yet
]
LARGE_SHAPES_AND_POWERS_AND_TILES = [
    # ([32], 2, 4),
    ([2, 32], 2, 4),
    # ([32], 3, 4),
    # ([64], 2, 8),
    ([8,16], 2, 8),
    # ([128,16], 3, 4),
    # ([128,32], 4, 2),
    ([128,32], 3, 1),
    ([128,4,32], 4, 2),
    # ([64,32,16], 2, 1), # mosaic fails with > 1 batch dimension due to some cpp error
    # ([64,32,8], 3, 8),  # mosaic fails with > 1 batch dimension due to some cpp error
]


@pytest.mark.parametrize("X_shape,p,_", SHAPES_AND_POWERS_AND_TILES)
def test_tpow(X_shape, p, _):
    x = th.empty(X_shape)
    Y = tpow(x, p)
    assert Y.shape == tpow_shape(X_shape, p)

def _test_op(X_shape, p, d_tile, duplicate_correction):
    X = th.randn(X_shape, device='cuda')
    Z = op(X, p, d_tile, duplicate_correction)
    assert Z.shape == op_output_shape(X_shape, p, d_tile)
    Z_ref = op_reference(X, p, d_tile, duplicate_correction)
    diff(Z, Z_ref, rtol=4e-2, atol=1e-2)
@pytest.mark.parametrize("X_shape,p,d_tile", SHAPES_AND_POWERS_AND_TILES)
@pytest.mark.parametrize("duplicate_correction", [True, False])
def test_op_small(X_shape, p, d_tile, duplicate_correction):
    _test_op(X_shape, p, d_tile, duplicate_correction)
@pytest.mark.parametrize("X_shape,p,d_tile", LARGE_SHAPES_AND_POWERS_AND_TILES)
def test_op_large(X_shape, p, d_tile):
    _test_op(X_shape, p, d_tile, True)

@pytest.mark.parametrize("X_shape,p,d_tile", SHAPES_AND_POWERS_AND_TILES)
def test_sympow_tpow_norm_equivalence(X_shape, p, d_tile):
    X = th.randn(X_shape, device='cuda')
    Y = tpow(X, p).flatten(start_dim=-p)
    Z = interface(X, p, d_tile, -1)
    diff(th.linalg.norm(Y, dim=-1), th.linalg.norm(Z, dim=-1), rtol=4e-2, atol=1e-2)
 

def _test_interface(X_shape, power, d_tile, dim):
    """Test SympowKernel with various shapes and configurations."""
    if dim >= len(X_shape): return # Skip if dim is out of bounds
    X = th.randn(th.Size(X_shape), device="cuda")
    Z = interface(X, power, d_tile, dim)
    assert Z.shape == interface_output_shape(X_shape, power, d_tile, dim)
@pytest.mark.parametrize("X_shape,power,d_tile", SHAPES_AND_POWERS_AND_TILES)
def test_interface_small(X_shape, power, d_tile):
    for dim in range(len(X_shape)):
        if X_shape[dim] % d_tile != 0: continue # can't expand this dimension
        _test_interface(X_shape, power, d_tile, dim)
@pytest.mark.parametrize("X_shape,power,d_tile", LARGE_SHAPES_AND_POWERS_AND_TILES)
def test_interface_large(X_shape, power, d_tile):
    _test_interface(X_shape, power, d_tile, -1)

@pytest.mark.parametrize("X_shape,power,d_tile", [
    ([1, 32], 2, 4),
    ([128,32], 3, 1),
    ([8,16], 4, 8),
])
@pytest.mark.parametrize("perm", PERMUTATIONS_OF_STRIDES_UP_TO_4D)
def test_permuted_strides(X_shape, power, d_tile, perm):
    X = th.randn(th.Size(X_shape), device="cuda")
    Z = th.empty(op_output_shape(X_shape, power, d_tile), device="cuda")
    # Create new x tensors with non-standard strides
    X_strided = create_permuted_strides_layout(X, perm)
    Z_strided = create_permuted_strides_layout(Z, perm)
    # the autotuned binding should be invariant to the strides
    binding_autotuned(Z, X, power, d_tile, duplicate_correction=True)
    binding_autotuned(Z_strided, X_strided, power, d_tile, duplicate_correction=True)
    diff(Z, Z_strided, rtol=1e-3, atol=1e-3)

@pytest.mark.parametrize("X_shape, power, d_tile", LARGE_SHAPES_AND_POWERS_AND_TILES)
@pytest.mark.parametrize("duplicate_correction", [True, False])
def test_sympow_autograd_against_reference(X_shape, power, d_tile, duplicate_correction):
    """Test that sympow gradients match the reference implementation."""
    X = th.randn(X_shape, device="cuda", requires_grad=True)
    Z = op(X, power, d_tile, duplicate_correction)
    Zgrad = th.randn_like(Z)
    Z.backward(Zgrad)
    Xgrad = X.grad.clone()
    X.grad = None
    # Run forward and backward with reference implementation
    Z_ref = op_reference(X, power, d_tile, duplicate_correction)
    Z_ref.backward(Zgrad)
    Xgrad_ref = X.grad.clone()
    diff(Xgrad, Xgrad_ref, rtol=1e-3, atol=1e-3)
