import torch as th
from math import comb, factorial, sqrt, prod

def tprod(*xs) -> th.Tensor:
    batch_dims = tuple(xs[0].shape[:-1])
    for xi in xs:
        assert xi.shape[:-1] == batch_dims, f"batch_dims of xi={xi.shape[:-1]} do not match batch_dims={batch_dims}"
    y_shape = batch_dims + tuple([xi.shape[-1] for xi in xs])
    y = th.ones(y_shape, device=xs[0].device, dtype=xs[0].dtype)
    batch_slice = [slice(None)] * len(batch_dims)
    for i in range(len(xs)):
        feature_bcast: List[Union[None, slice]] = [None] * len(xs)
        feature_bcast[i] = slice(None)
        y *= xs[-i-1][batch_slice + feature_bcast]
    return y

def tpow(x, power: int) -> th.Tensor:
    return tprod(*([x]*power))

def tprod_bcast(x, power, dim) -> th.Tensor:
    batch_dims = tuple(x.shape[:-1])
    batch_slice = [slice(None)] * len(batch_dims)
    feature_bcast: List[Union[None, slice]] = [None] * power
    feature_bcast[dim] = slice(None)
    x_bcast = x[batch_slice + feature_bcast]
    return x_bcast

def tprod_bwd(xis, zgrad, power):
    b_dims = len(zgrad.shape) - power
    xigrads = []
    for i in range(power):
        v = zgrad.clone()
        for j in range(power):
            if j != i: v = v * tprod_bcast(xis[-j-1], power, j)
        reduce_dims = [j+b_dims for j in range(power) if j != i]
        xigrad_delta = th.sum(v, dim=tuple(reduce_dims))
        xigrads.append(xigrad_delta)
    return xigrads

def tpow_shape(x_shape, power):
    return th.Size(tuple(x_shape[:-1]) + (x_shape[-1],) * power)

def default_d_tile(d, power):
    """
    Returns the default d_tile for a given d and power.
    """
    default_d_tiles = {
        16: {
            2: 4,
            3: 4,
            4: 2,
        },
        32: {
            2: 8,
            3: 4,
            4: 2
        },
        64: {
            2: 8,
            3: 4,
            4: 2
        }
    }
    try:
        return default_d_tiles[d][power]
    except KeyError:
        return 1

def diff(a, b, rtol=None, atol=None, assert_close=True, verbose=True, title=None):
    """ A diff function that helps debug numerical issues

    Args:
        a: torch.Tensor
        b: torch.Tensor
        rtol: float
        atol: float
        assert_close: bool
        verbose: bool
    Returns:
        bool: True if a and b are close, False otherwise
    """
    a = a.to(th.float32)
    b = b.to(th.float32)
    if rtol is None: rtol = 1e-3
    if atol is None: atol = 1e-3
    equal = th.allclose(a, b, rtol=rtol, atol=atol)
    error_max = th.max(th.abs(a - b))
    error_hist = th.histc(th.abs(a - b), bins=100, min=0, max=1)
    
    # Calculate absolute error
    abs_diff = th.abs(a - b)
    total_elements = a.numel()
    
    # Calculate relative error where b is non-zero
    b_nonzero = b != 0
    rel_diff = th.zeros_like(abs_diff)
    rel_diff[b_nonzero] = abs_diff[b_nonzero] / th.abs(b[b_nonzero])
    
    if verbose:
        print('\n' * 3)
        print('=' * 10 + f" {title} " + '=' * 10)
        print(f"Max absolute error: {error_max.item()}")
        print(f"Tensors are {'close' if equal else 'different'} according to torch.allclose")
        
        # Calculate thresholds for relative error table
        rel_thresholds = th.logspace(
            th.log10(th.tensor(rtol)), 
            0.0, 
            steps=10
        )
        
        # Calculate thresholds for absolute error table
        abs_thresholds = th.logspace(
            th.log10(th.tensor(atol)), 
            0.0, 
            steps=10
        )
        
        # Print relative error table
        print("\nRelative Error Table:")
        print("---------------------")
        print(f"{'Threshold':<12} {'% matched':<12} {'Element Count':<12}")
        print("-" * 36)
        for threshold in rel_thresholds:
            count = (rel_diff <= threshold).sum().item()
            percentage = 100.0 * count / total_elements
            print(f"{threshold.item():<12.6f} {percentage:<12.2f} {count:<12}")
        
        # Print absolute error table
        print("\nAbsolute Error Table:")
        print("---------------------")
        print(f"{'Threshold':<12} {'% matched':<12} {'Element Count':<12}")
        print("-" * 36)
        for threshold in abs_thresholds:
            count = (abs_diff <= threshold).sum().item()
            percentage = 100.0 * count / total_elements
            print(f"{threshold.item():<12.6f} {percentage:<12.2f} {count:<12}")
        
        # Print some examples of largest errors
        if not equal:
            n_samples = min(5, total_elements)
            print("\nLargest Errors:")
            flat_indices = th.argsort(abs_diff.flatten(), descending=True)[:n_samples]
            for i in range(n_samples):
                idx = flat_indices[i]
                multi_idx = th.unravel_index(idx, a.shape)
                multi_idx_str = ', '.join(map(str, [idx.item() for idx in multi_idx]))
                print(f"Index [{multi_idx_str}]: a={a[multi_idx].item()}, b={b[multi_idx].item()}, "
                      f"abs_diff={abs_diff[multi_idx].item()}, rel_diff={rel_diff[multi_idx].item()}")
    
    if assert_close:
        assert equal, f"Tensors are not close! Max absolute error: {error_max.item()}"
    
    return equal