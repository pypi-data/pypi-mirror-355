import torch as th
from vidrial.kernels.mma_sympow_bwd.binding import autotuned

@th.library.custom_op("mosaic::mma_sympow_bwd", mutates_args=())
def op(A: th.Tensor, B: th.Tensor, c: th.Tensor, expand_dim: int, power: int, d_tile: int, duplicate_correction: bool = True) -> th.Tensor:
    c_dot = th.empty_like(c)
    autotuned(A, B, c, c_dot, expand_dim, power, d_tile, duplicate_correction)
    return c_dot

@op.register_fake
def op_fake(A: th.Tensor, B: th.Tensor, c: th.Tensor, expand_dim: int, power: int, d_tile: int, duplicate_correction: bool = True):
    return th.empty_like(c)