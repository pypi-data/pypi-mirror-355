import pytest
import torch as th
from vidrial.kernels.sympow.dimensions import sympow_dim
from vidrial.mosaic.utils.test_utils import diff, PERMUTATIONS_OF_STRIDES_UP_TO_4D, create_permuted_strides_layout
from vidrial.kernels.sympow.interface import interface as sympow
from vidrial.kernels.sympow.interface import interface_reference as sympow_reference
from vidrial.kernels.sympow_mma.binding import binding_autotuned
from vidrial.kernels.sympow_mma.op import op, op_reference

PROBLEM_SHAPES = [
    (1, 16, 64, 32, 2, 8, False),
    (16, 16, 64, 32, 2, 8, True),
    (10, 16, 1, 32, 2, 8, True),
    (2, 16, 64, 1, 2, 8, True),
    (4, 32, 10, 4, 3, 4, True),
    (6, 64, 1, 128, 2, 8, True),
]

@pytest.mark.parametrize("P,d,N,R,p,d_tile,duplicate_correction", PROBLEM_SHAPES)
@pytest.mark.parametrize("expand_dim", [
    1,
    2
])
def test_binding_autotuned(P, d, N, R, p, d_tile, expand_dim, duplicate_correction):
    D = sympow_dim(d, p, d_tile)
    M, K = {1: (D, R), 2: (R, D)}[expand_dim]
    A_shape = {1: (P, d, K), 2: (P, M, d)}[expand_dim]
    A = th.randn(A_shape, device="cuda")
    B = th.randn((P, K, N), device="cuda")
    C = th.randn((P, M, N), device="cuda")
    binding_autotuned(A, B, C, expand_dim, p, d_tile, duplicate_correction)
    eA_ref = sympow_reference(A, p, d_tile, expand_dim, duplicate_correction)
    C_ref = eA_ref @ B
    diff(C, C_ref, atol=1e-1, rtol=1e-1)

@pytest.mark.parametrize("P,d,N,R,p,d_tile,duplicate_correction", PROBLEM_SHAPES)
@pytest.mark.parametrize("expand_dim", [
    1,
    2
])
def test_op(P, d, N, R, p, d_tile, expand_dim, duplicate_correction):
    D = sympow_dim(d, p, d_tile)
    M, K = {1: (D, R), 2: (R, D)}[expand_dim]
    A_shape = {1: (P, d, K), 2: (P, M, d)}[expand_dim]
    A = th.randn(A_shape, device="cuda", requires_grad=True)
    B = th.randn((P, K, N), device="cuda", requires_grad=True)
    dC = th.randn((P, M, N), device="cuda")

    C = op(A, B, expand_dim, p, d_tile, duplicate_correction)
    C.backward(dC)
    assert A.grad is not None and B.grad is not None
    dA, dB = A.grad.clone(), B.grad.clone()
    A.grad, B.grad = None, None

    C_ref = op_reference(A, B, expand_dim, p, d_tile, duplicate_correction)
    C_ref.backward(dC)
    assert A.grad is not None and B.grad is not None
    dA_ref, dB_ref = A.grad.clone(), B.grad.clone()
    A.grad, B.grad = None, None

    diff(C, C_ref, atol=1e-1, rtol=1e-1)
    diff(dA, dA_ref, atol=1e-1, rtol=1e-1)
    diff(dB, dB_ref, atol=1e-1, rtol=1e-1)
