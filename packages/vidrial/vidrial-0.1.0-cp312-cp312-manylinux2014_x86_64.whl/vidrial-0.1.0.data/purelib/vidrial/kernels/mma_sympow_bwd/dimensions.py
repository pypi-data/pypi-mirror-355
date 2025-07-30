import torch as th
from vidrial.kernels.sympow.dimensions import sympow_dim

def dimensions(A_shape, B_shape, c_shape, power, d_tile):
    """ Checks that the tensors satisfy the shape assumptions and return the problem dimensions """
    P, M, K, N, d =  A_shape[-3], A_shape[-2], A_shape[-1], B_shape[-1], c_shape[-2]
    D = sympow_dim(d, power, d_tile)
    assert M == D, "since expand_dim=-1, "
    assert A_shape == (P, M, K)
    assert B_shape == (P, K, N)
    assert c_shape == (P, d, N)
    return P, M, K, N, d

def output_shape(A_shape, B_shape, c_shape, power, d_tile):
    dimensions(A_shape, B_shape, c_shape, power, d_tile) # checks that the dimensions are valid
    return c_shape
 
def canonical_inputs(A, B, c, c_dot, expand_dim):
    """ Make all the arguments 3D and ensure expand_dim indexes with negative values """
    assert expand_dim == -2, f"{expand_dim} not implemented yet. Current cuda kernel only supports expanding -2"
    assert A.dtype == B.dtype == c.dtype == c_dot.dtype, f"Invalid {A.dtype}, {B.dtype}, {c.dtype}, {c_dot.dtype}. Kernel currently assumes all input tensors have the same dtype"
    assert A.ndim == B.ndim == c.ndim == c_dot.ndim, f"Invalid {A.ndim}, {B.ndim}, {c.ndim}, {c_dot.ndim}. Kernel currently assumes all input tensors have the same number of dimensions"
    assert A.ndim in (2, 3), f"Invalid {A.ndim}. Kernel currently only supports 2D and 3D input tensors, generic batching not implemented yet"
    if A.ndim == 2: #  the input tensors such that they are all 3D. Also computes the relevant dimensions
        assert B.ndim == c.ndim == c_dot.ndim == 2, f"Invalid {A.ndim}, {B.ndim}, {c.ndim}, {c_dot.ndim}. Kernel currently only supports 2D input tensors"
        A, B, c, c_dot = map(lambda t: th.unsqueeze(t, 0), (A, B, c, c_dot))
        expand_dim += 1
    if expand_dim >= 0: # make expand_dim negative (eg 2 -> -1)
        expand_dim -= 3
        assert expand_dim < 0
    return A, B, c, c_dot, expand_dim
