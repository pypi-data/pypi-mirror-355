import torch as th
from math import sqrt
from vidrial.jit.mosaic_types.types import Shape, Layout, Int
from vidrial.kernels.sympow.dimensions import problem_dimensions, op_output_shape, SympowCoords
from vidrial.kernels.sympow.binding import binding_autotuned
from vidrial.kernels.sympow_bwd.op import op as sympow_bwd
from vidrial.mosaic.utils.common import tprod


# ---------------------- Op --------------------------------

@th.library.custom_op("mosaic::sympow", mutates_args=())
def op(X: th.Tensor, power: int, d_tile: int, duplicate_correction: bool = True) -> th.Tensor:
    """ Computes the tiled symmetric power of X.
    Dimensions:
        d the feature dimension being powered.
        bs=[b0, b1, ...] the batch dimensions.
        D the expanded dimension. Given by sympow_dim(d, power, d_tile)
    Args:
        X: Input tensor of shape `(b0, b1, ..., d)`.
        power: Power of the symmetric power.
        d_tile: Tile size for the operation.
        duplicate_correction: Whether to correct for duplicate elements.
    Returns:
        Z: Output tensor of shape `(b0, b1, ..., nt, dt, dt, ...,)`. Where dt = d_tile and
           nt is the number of tiles.
    """
    expand_batch = True if X.dim() == 1 else False # expand a batch dimension if there is none
    if expand_batch: X = X.unsqueeze(0)
    assert X.device.type == "cuda", "X must be on GPU"
    Z = th.empty(op_output_shape(X.shape, power, d_tile), device=X.device, dtype=X.dtype)
    binding_autotuned(Z, X, power, d_tile, duplicate_correction)
    if expand_batch: Z = Z[0]
    return Z

@op.register_fake
def op_fake(X: th.Tensor, power: int, d_tile: int, duplicate_correction: bool = True):
    return th.empty(op_output_shape(X.shape, power, d_tile), device=X.device, dtype=X.dtype)


# ---------------------- Autograd --------------------------------

def setup_context(ctx, inputs, output):
    X, power, d_tile, duplicate_correction = inputs
    ctx.save_for_backward(X)
    ctx.power = power
    ctx.d_tile = d_tile
    ctx.duplicate_correction = duplicate_correction
def op_backward(ctx, dZ):
    X, = ctx.saved_tensors
    dX = sympow_bwd(X, dZ, ctx.power, ctx.d_tile, ctx.duplicate_correction)
    return dX, None, None, None
th.library.register_autograd(
    "mosaic::sympow", op_backward, setup_context=setup_context
)


# ---------------------- Reference Op  --------------------------------

def op_reference(X: th.Tensor, power: int, d_tile: int, duplicate_correction: bool = True) -> th.Tensor:
    expand_batch = True if X.dim() == 1 else False
    if expand_batch: X = X.unsqueeze(0)
    Z = th.empty(op_output_shape(X.shape, power, d_tile), device=X.device, dtype=X.dtype)
    bs, d, D = problem_dimensions(Z.shape, X.shape, power, d_tile)
    batch_slice = (slice(None),) * len(bs)
    x_tiled = X.reshape(bs + (-1, d_tile))
    for idx, seq, dup in SympowCoords(d // d_tile, power):
        z_tile = Z[batch_slice + (idx,)]
        x_tiles = [x_tiled[batch_slice + (seq[i],)] for i in range(power)]
        z_tile[:] = tprod(*x_tiles)
        if duplicate_correction: z_tile[:] *= sqrt(dup)
    if expand_batch: Z = Z[0]
    return Z
