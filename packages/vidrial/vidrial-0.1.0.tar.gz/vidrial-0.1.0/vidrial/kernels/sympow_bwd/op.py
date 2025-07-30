import torch as th
from math import sqrt
from vidrial.kernels.sympow.dimensions import op_output_shape as fwd_op_output_shape, problem_dimensions, SympowCoords
from vidrial.kernels.sympow_bwd.binding import binding_autotuned
from vidrial.mosaic.utils.common import tprod_bwd


# ---------------------- Op --------------------------------

@th.library.custom_op('mosaic::sympow_bwd', mutates_args=(), device_types='cuda')
def op(X: th.Tensor, Zgrad: th.Tensor, power: int, d_tile: int, duplicate_correction: bool = True) -> th.Tensor:
    """ Computes gradient wrt X of Z = sympow(X)
    Inputs:
        X: [b0, b1, ..., d] - Batch dimensions, feature dimension
        Zgrad: [b0, b1, ..., tn, dt, dt, ...] where dt = d_tile and tn is the tile number
        power: int - Power of the symmetric power
        d_tile: int - Tile size
        duplicate_correction: bool - Whether to use duplicate correction
    Output shape:
        Xgrad: [b0, b1, ..., d] - Gradient with respect to input X
    """
    Xgrad = th.empty_strided(X.size(), X.stride(), dtype=X.dtype, device=X.device)
    binding_autotuned(X, Zgrad, Xgrad, power, d_tile, duplicate_correction)
    return Xgrad

# Fake implementation for tracing and testing
@op.register_fake
def op_fake(X: th.Tensor, Zgrad: th.Tensor, power: int, d_tile: int, duplicate_correction: bool = True):
    return th.empty_like(X)


# ---------------------- Reference Op  --------------------------------

def op_reference(X: th.Tensor, Zgrad: th.Tensor, power: int, d_tile: int, duplicate_correction: bool = True) -> th.Tensor:
    Xgrad = th.zeros_like(X)
    bs, d, D = problem_dimensions(Zgrad.shape, X.shape, power, d_tile)
    batch_slice = (slice(None),) * len(bs)
    X_tiled = X.reshape(bs + (-1, d_tile))
    Xgrad_tiled = Xgrad.reshape(bs + (-1, d_tile))
    for idx, seq, dup in SympowCoords(d // d_tile, power):
        Zgrad_tile = Zgrad[batch_slice + (idx,)].clone()
        if duplicate_correction: Zgrad_tile[:] *= sqrt(dup)
        X_tiles = [X_tiled[batch_slice + (seq[i],)] for i in range(power)]
        Xgrad_tiles = tprod_bwd(X_tiles, Zgrad_tile, power)
        for i in range(power):
            Xgrad_tile = Xgrad_tiled[batch_slice + (seq[-i-1],)]
            Xgrad_tile += Xgrad_tiles[i]
    return Xgrad

