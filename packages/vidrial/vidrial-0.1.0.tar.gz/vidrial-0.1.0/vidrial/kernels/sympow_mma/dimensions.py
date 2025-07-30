from vidrial.kernels.sympow.dimensions import sympow_dim, sympow_shape

def problem_shape(A_shape, B_shape, C_shape, expand_dim, power, d_tile) -> tuple[int, int, int, int, int, int]:
    assert len(A_shape) == len(B_shape) == len(C_shape) == 3
    P, M, N, K, d = C_shape[0], C_shape[1], C_shape[2], B_shape[1], A_shape[expand_dim]
    D = sympow_dim(d, power, d_tile)
    eA_shape = sympow_shape(A_shape, power, d_tile, expand_dim)
    assert expand_dim % 3 in [1,2], f"expand_dim={expand_dim} must be 1 or 2 (expand M or K)"
    assert A_shape == tuple(d if i==expand_dim % 3 else v for i, v in enumerate((P,M,K)))
    assert eA_shape == (P, M, K)
    assert B_shape == (P, K, N)
    assert C_shape == (P, M, N)
    return P, M, N, K, d, D

def op_output_shape(A_shape, B_shape, expand_dim, power, d_tile) -> tuple[int, int, int]:
    P, K, N = B_shape
    d = A_shape[expand_dim]
    M = A_shape[1] if expand_dim % 3 != 1 else sympow_dim(d, power, d_tile)
    C_shape = (P, M, N)
    problem_shape(A_shape, B_shape, C_shape, expand_dim, power, d_tile) # Check that the shape is valid
    return C_shape
