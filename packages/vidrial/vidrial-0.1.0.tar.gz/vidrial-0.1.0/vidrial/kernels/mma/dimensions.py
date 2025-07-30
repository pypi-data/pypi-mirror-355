from typing import Tuple

def problem_shape(A_shape, B_shape, C_shape=None) -> Tuple[int, int, int, int]:
    assert len(A_shape) == len(B_shape) == 3
    if C_shape is not None: assert len(A_shape) == len(C_shape)
    P, M, N, K = A_shape[0], A_shape[-2], B_shape[-1], A_shape[-1]
    assert A_shape == (P, M, K)
    assert B_shape == (P, K, N)
    if C_shape is not None: assert C_shape == (P, M, N)
    return P, M, N, K

