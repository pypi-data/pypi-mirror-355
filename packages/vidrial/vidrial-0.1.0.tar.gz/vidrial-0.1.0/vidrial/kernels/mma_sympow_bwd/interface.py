import torch as th
from vidrial.kernels.sympow.dimensions import sympow_op_shape, sympow_dim
from vidrial.kernels.mma_sympow_bwd.op import op
from vidrial.kernels.sympow_bwd.op import op_reference as sympow_bwd_op_reference

def interface(A, B, c, expand_dim, power, d_tile, duplicate_correction=True):
    """ First computes C_dot=A@B matmul and then c_dot = sympow_bwd(c, C_dot)
        (operation is used to implement mma_sympow_bwd)
    The kernel assumes M=D=sympow_dim(d, power, d_tile)
    Arguments:
      A: [P, M, K]
      B: [P, N, K]
      c: [P, d, N]
    Returns:
      c_dot: [P, d, N]
    """
    expand_dim = expand_dim if expand_dim < 0 else expand_dim - A.ndim
    assert expand_dim in [-2, -1], f"expand_dim={expand_dim} invalid. Only M,N dimensions can be expanded"
    transpose = expand_dim == -1 # the op only accepts expand_dim=-2. To handle -1 we need to transpose M and N
    if transpose:
        expand_dim = -2
        c = c.transpose(-1, -2)
        A, B = B.transpose(-1,-2), A.transpose(-1,-2)
    c_dot = op(A, B, c, expand_dim, power, d_tile, duplicate_correction)
    if transpose:
        c_dot = c_dot.transpose(-1, -2)
    return c_dot


def interface_reference(A, B, c, expand_dim, power, d_tile, duplicate_correction=True):
    transpose = expand_dim == -2 # tiled_sympow_bwd_reference_ assumes that expand_dim=-1 (the N dim)
    if transpose: 
        expand_dim = -1
        c = c.transpose(-1, -2)
        A, B = B.transpose(-1,-2), A.transpose(-1,-2)
    C_dot = A @ B 
    C_dot = C_dot.reshape(sympow_op_shape(c.shape, power, d_tile))
    c_dot = sympow_bwd_op_reference(c, C_dot, power, d_tile, duplicate_correction)
    if transpose:
        c_dot = c_dot.transpose(-1, -2)
    return c_dot

