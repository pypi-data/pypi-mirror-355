import torch
from vidrial.jit.compiler import compile


def test_add_one(get_add_one_kernel_code):
    X = torch.randn(64, 64, device="cuda")
    Y = torch.empty_like(X)
    code = get_add_one_kernel_code(X, Y)
    runtime = compile(code)
    runtime(X, Y)
    torch.testing.assert_close(X + 1, Y)
