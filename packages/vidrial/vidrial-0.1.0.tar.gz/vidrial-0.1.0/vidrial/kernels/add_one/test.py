import torch as th
import pytest
import time
from vidrial.kernels.add_one.add_one import add_one_kernel

# To run with all the JIT logs: export JIT_VERBOSE=1; uv run pytest -s

def test_add_one_basic():
    """Test basic functionality of add_one."""
    V = th.ones(32, 32, dtype=th.float32, device="cuda")
    V_ref = V + 1
    
    add_one_kernel(V)
    
    assert V.shape == (32, 32)
    assert V.dtype == th.float32
    assert V.device.type == "cuda"
    assert th.allclose(V, V_ref, rtol=1e-5, atol=1e-5)
