from math import sqrt
import pytest
import torch as th
from vidrial.jit.mosaic_types.shape import Shape
from vidrial.mosaic.utils.common import diff
from vidrial.kernels.mma.binding import binding, binding_autotuned
from vidrial.kernels.mma.op import op, op_reference


@pytest.mark.parametrize("P,M,N,K", [
    (1, 16, 8, 16),
    (4, 16, 8, 16),
])
@pytest.mark.parametrize("dtype", [
    th.float16,
    th.bfloat16,
    th.float32, # kernel error with float32 & tf32
])
def test_binding_autotuned(P, M, N, K, dtype):
    """Test raw_mma kernel on GPU."""
    A = th.randn(P, M, K, dtype=dtype, device="cuda") / sqrt((M+K)/2)
    B = th.randn(P, K, N, dtype=dtype, device="cuda") / sqrt((K+N)/2)
    C = th.empty(P, M, N, dtype=dtype, device="cuda") / sqrt((M+N)/2)
    binding_autotuned(A, B, C)
    C_ref = A @ B
    diff(C, C_ref, 1e-1)

@pytest.mark.parametrize("P,M,N,K", [
    (1, 16, 64, 32),
    (16, 32, 32, 32),
])
@pytest.mark.parametrize("dtype", [
    th.float16,
    th.bfloat16,
    th.float32, # kernel error with float32 & tf32
])
def test_binding(P, M, N, K, dtype):
    """Test raw_mma kernel with sweep of tileshapes and atom placements"""
    if dtype == th.float16:
        atom = "SM80_16x8x8_F32F16F16F32_TN"
    elif dtype == th.bfloat16:
        atom = "SM80_16x8x8_F32BF16BF16F32_TN"
    elif dtype == th.float32:
        atom = "SM80_16x8x4_F32TF32TF32F32_TN"
    else:
        raise ValueError(f"Unsupported dtype: {dtype}")
    configs = [
        {
            "MNKTileShape": Shape(16, 32, 16),
            "MNKAtomPlacement": Shape(1, 1, 1),
            "Atom": atom,
        },
        {
            "MNKTileShape": Shape(16, 16, 16),
            "MNKAtomPlacement": Shape(1, 1, 1),
            "Atom": atom,
        },
    ]
    A = th.randn(P, M, K, dtype=dtype, device="cuda") / sqrt((M+K)/2)
    B = th.randn(P, K, N, dtype=dtype, device="cuda") / sqrt((K+N)/2)
    C = th.empty(P, M, N, dtype=dtype, device="cuda") / sqrt((M+N)/2)
    C_ref = A @ B
    for config in configs:
        C[:] = 0
        binding(A, B, C, config["Atom"], config["MNKTileShape"], config["MNKAtomPlacement"], 1, 1, True, 1)
        diff(C, C_ref, 1e-1)


@pytest.mark.parametrize("batch_dims,M,N,K", [
    ((), 16, 16, 16),
    ((4,), 64, 64, 64),
    ((8,), 32, 64, 32),
    ((16,), 64, 32, 64),
])
def test_mma_autograd_against_reference(batch_dims, M, K, N):
    """Test that mma gradients match PyTorch's native implementation."""
    dtype = th.float16
    device = 'cuda'
    generator = th.Generator(device=device).manual_seed(42)
    A = th.randn(batch_dims + (M, K), dtype=dtype, device=device, generator=generator, requires_grad=True)
    B = th.randn(batch_dims + (K, N), dtype=dtype, device=device, generator=generator, requires_grad=True)
    dC = th.randn(batch_dims + (M, N), dtype=dtype, device=device, generator=generator, requires_grad=True)
    # Custom op fwd and bwd 
    C = op(A, B)
    C.backward(dC)
    assert A.grad is not None and B.grad is not None
    dA = A.grad.clone()
    dB = B.grad.clone()
    A.grad, B.grad = None, None
    # Reference op fwd and bwd 
    C_ref = op_reference(A, B)
    C_ref.backward(dC)
    assert A.grad is not None and B.grad is not None
    dA_ref = A.grad.clone()
    dB_ref = B.grad.clone()
    # Compare results
    diff(C, C_ref, 1e-1)
    diff(dA, dA_ref, 1e-1)
    diff(dB, dB_ref, 1e-1)

# TODO: test with torch.compile