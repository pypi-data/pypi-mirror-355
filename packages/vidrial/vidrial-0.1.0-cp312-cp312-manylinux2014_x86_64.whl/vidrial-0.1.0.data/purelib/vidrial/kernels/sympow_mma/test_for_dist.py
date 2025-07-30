import pytest
import torch as th
from vidrial.kernels.sympow.dimensions import sympow_dim
from vidrial.mosaic.utils.test_utils import diff
from vidrial.kernels.sympow.interface import interface as sympow
from vidrial.kernels.sympow_mma.op import op as sympow_mma

# b, t, d, p, d_tile, duplicate_correction
ALL_PROBLEMS = [
    (b, t, d, e, p, d_tile, True, expand_dim, dtype)
    for d, e, p, d_tile in [(64, 64, 2, 8), (64, 1, 2, 8)]
    for b in [16, 8, 4, 2, 1, 32, 64, 128]
    for t in [1024, 4096]
    for expand_dim in [-1, -2]
    for dtype in [th.bfloat16]
]

# ---- Check sympow_mma == sympow_expand + mma on GPU ----
@pytest.mark.parametrize("b, t, d, e, p, d_tile, duplicate_correction, expand_dim, dtype", ALL_PROBLEMS, ids=str)
def test_sympow_expandA_mma(b, t, d, e, p, d_tile, duplicate_correction, expand_dim, dtype):
    D = sympow_dim(d, p, d_tile)
    if expand_dim == -2: # expand M
        A = th.randn(b, d, t, dtype=dtype, device="cuda", requires_grad=True) * 1e-3
        B = th.randn(b, t, e, dtype=dtype, device="cuda", requires_grad=True) * 1e-3
        A_ref = A.detach().clone().requires_grad_(True)
        B_ref = B.detach().clone().requires_grad_(True)
    else: # expand K
        A = th.randn(b, t, d, dtype=dtype, device="cuda", requires_grad=True) * 1e-3
        B = th.randn(b, D, e, dtype=dtype, device="cuda", requires_grad=True) * 1e-3
        A_ref = A.detach().clone().requires_grad_(True)
        B_ref = B.detach().clone().requires_grad_(True)

    for t in [A, B, A_ref, B_ref]:
        t.retain_grad()

    C = sympow_mma(A, B, expand_dim, p, d_tile, duplicate_correction)
    assert C.shape == (b, D, e) if expand_dim == -2 else (b, t, e)
    eA = sympow(A_ref, p, d_tile, expand_dim, duplicate_correction)
    C_ref = eA @ B_ref
    diff(C, C_ref, verbose=True, atol=1e-1, rtol=1e-2)

    th.autograd.backward(C_ref, th.ones_like(C_ref))
    th.autograd.backward(C, th.ones_like(C))

    diff(A.grad, A_ref.grad, verbose=True, atol=1e-1, rtol=1e-2)
    diff(B.grad, B_ref.grad, verbose=True, atol=1e-1, rtol=1e-2)
    
