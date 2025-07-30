import pytest
import torch as th
from vidrial.kernels.sympow.dimensions import sympow_dim
from vidrial.jit.mosaic_types.types import Shape, Layout, Int
from vidrial.kernels.mma_sympow_bwd.binding import binding, autotuned
from vidrial.kernels.mma_sympow_bwd.interface import interface, interface_reference
from vidrial.mosaic.utils.common import diff

def test_binding():
    d, power, d_tile = 64, 2, 8
    D = sympow_dim(d, power, d_tile)
    M, N, K, P = D, 16, 32, 8
    A = th.randn((P, M, K), device="cuda")
    B = th.randn((P, K, N), device="cuda")
    c = th.randn((P, d, N), device="cuda")
    c_dot = th.empty((P, d, N), device="cuda")
    binding(
        A, B, c, c_dot, -2, power, d_tile, 
        duplicate_correction=True,
        MNKTileShape=Shape(Int(64), Int(16), Int(32)), 
        MNKAtomPlacement=Shape(Int(1), Int(1), Int(1)), 
        Atom="SM80_16x8x8_F16F16F16F16_TN", 
        smempipe=1, 
        regpipe=2, 
        use_ldsm=True, 
        swizzle=0
    )
    # call autotuned kernel
    autotuned(A, B, c, c_dot, -2, power, d_tile, duplicate_correction=True)

def test_call_interface_expand_M():
    d, power, d_tile = 64, 2, 8
    D = sympow_dim(d, power, d_tile)
    M, N, K, P = D, 16, 32, 8
    A = th.randn((P, M, K), device="cuda")
    B = th.randn((P, K, N), device="cuda")
    c = th.randn((P, d, N), device="cuda")
    c_dot = interface(A, B, c, -2, power, d_tile)

def test_call_interface_expand_N():
    d, power, d_tile = 64, 2, 8
    D = sympow_dim(d, power, d_tile)
    M, N, K, P = 16, D, 32, 8
    A = th.randn((P, M, K), device="cuda")
    B = th.randn((P, K, N), device="cuda")
    c = th.randn((P, M, d), device="cuda")
    c_dot = interface(A, B, c, -1, power, d_tile)

@pytest.mark.parametrize("d, power, d_tile, N, K, P", [
    (4, 2, 4, 8, 8, 1),
    (64, 2, 8, 64, 128, 4),
    (64, 2, 1, 64, 1, 128)
])
def test_interface_matches_reference(d, power, d_tile, N, K, P):
    M = sympow_dim(d, power, d_tile)
    A = th.randn((P, M, K), device="cuda")
    B = th.randn((P, K, N), device="cuda")
    c = th.randn((P, d, N), device="cuda")
    c_dot = interface(A, B, c, -2, power, d_tile)
    c_dot_ref = interface_reference(A, B, c, -2, power, d_tile)
    diff(c_dot, c_dot_ref, atol=1e-1, rtol=1e-1)#, verbose=True)
