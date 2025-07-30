from vidrial.kernels.sympow.op import op, op_reference

def interface(X, power, d_tile=1, dim=-1, duplicate_correction=True):
    """ Computes the tiled symmetric power of X.
    Dimensions:
        d the feature dimension being powered.
        b the batch dimensions
        D the expanded dimension. Given by sympow_dim(d, power, d_tile)
    Args:
        X: Input tensor of shape `[d0, d1, ...]`.
        power: Power of the symmetric power.
        d_tile: Tile size for the operation.
        duplicate_correction: Whether to correct for duplicate elements.
    Returns:
        Z: Same shape as X except that the dimension at position `dim` is expanded to D
           for example, if dim=0 Z is [D, d1, d2, ...]
    """
    n = len(X.shape)
    if dim >= 0: dim -= n
    assert dim < 0
    X = X.transpose(-1, dim) # Place the expand dim at the end (convention used in the op)
    Z = op(X, power, d_tile, duplicate_correction)
    Z = Z.reshape(X.shape[:-1] + (-1,)) # Flatten tile_count, d_tile, d_tile, ...
    return Z.transpose(-1, dim)

def interface_reference(X, power, d_tile=1, dim=-1, duplicate_correction=True):
    n = len(X.shape)
    if dim >= 0: dim -= n
    assert dim < 0
    X = X.transpose(-1, dim) # Place the expand dim at the end (convention used in the op)
    Z = op_reference(X, power, d_tile, duplicate_correction)
    Z = Z.reshape(X.shape[:-1] + (-1,)) # Flatten tile_count, d_tile, d_tile, ...
    return Z.transpose(-1, dim)