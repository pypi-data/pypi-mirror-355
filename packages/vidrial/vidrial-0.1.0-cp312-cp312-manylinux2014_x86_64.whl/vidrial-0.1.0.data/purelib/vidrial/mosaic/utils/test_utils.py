import torch

# 24 permutations of strides up to 4D
PERMUTATIONS_OF_STRIDES_UP_TO_4D = [
    (0, 1, 2, 3),
    # (0, 1, 3, 2),
    # (0, 2, 1, 3),
    # (0, 2, 3, 1),
    # (0, 3, 1, 2),
    # (0, 3, 2, 1),
    # (1, 0, 2, 3),
    # (1, 0, 3, 2),
    # (1, 2, 0, 3),
    (1, 2, 3, 0),
    # (1, 3, 0, 2),
    # (1, 3, 2, 0),
    # (2, 0, 1, 3),
    # (2, 0, 3, 1),
    # (2, 1, 0, 3),
    # (2, 1, 3, 0),
    # (2, 3, 0, 1),
    # (2, 3, 1, 0),
    # (3, 0, 1, 2),
    # (3, 0, 2, 1),
    (3, 1, 0, 2),
    # (3, 1, 2, 0),
    # (3, 2, 0, 1),
    (3, 2, 1, 0),
]

def create_standard_layout(tensor):
    """
    Standard contiguous layout (C-contiguous):
    - Elements in the innermost dimension are adjacent in memory
    - Row-major order: rows are stored contiguously
    - Default PyTorch layout with strides that decrease from left to right
    - Fastest access pattern when iterating through the last dimension first
    """
    return tensor.clone().contiguous()

def create_strided_layout(tensor):
    """
    Strided layout with gaps:
    - Contains same data but with deliberate gaps in memory
    - Non-standard strides that don't match either C or F contiguous patterns
    - Tests kernel's ability to handle arbitrary stride patterns
    - Good for detecting stride-related bugs in kernels assuming contiguity
    """
    # Handle 1D tensors specially
    if tensor.dim() == 1:
        size = tensor.size(0)
        # Create tensor with gaps
        padded = torch.zeros(size * 2, dtype=tensor.dtype, device=tensor.device)
        padded[::2] = tensor  # Place values at even indices
        return padded[::2]    # Return view with same values but different stride

    # For 2D+ tensors
    shape = list(tensor.shape)
    padded_shape = shape.copy()
    padded_shape[1] = shape[1] * 2  # Double size in dimension 1

    padded = torch.zeros(padded_shape, dtype=tensor.dtype, device=tensor.device)
    padded[:, ::2, ...] = tensor     # Place at even indices of dimension 1
    return padded[:, ::2, ...]       # Return view with same values but different stride

def create_permuted_strides_layout(tensor, permutation):
    """
    Creates a tensor with permuted strides while maintaining the same logical indexing.
    
    Args:
        tensor (torch.Tensor): Input tensor to permute strides for
        permutation (list): List of integers representing the desired stride order.
                          Can include indices >= tensor.dim() which will be ignored.
                          If shorter than tensor.dim(), remaining dimensions will be kept in order.
    
    Returns:
        torch.Tensor: A new tensor with permuted strides but same logical indexing
        
    Example:
        >>> x = torch.randn(2, 3, 4)
        >>> # Permute strides to be [dim2, dim0, dim1]
        >>> y = create_permuted_strides_layout(x, [2, 0, 1])
    """
    # Extend permutation to match tensor dimensions if needed
    if len(permutation) < tensor.dim():
        permutation = list(permutation) + list(range(len(permutation), tensor.dim()))

    # Filter out invalid permutation indices
    valid_perm = [p for p in permutation if p < tensor.dim()]

    # If permutation is empty or all indices are invalid, return original tensor
    if not valid_perm:
        return tensor.clone()

    # First permute the dimensions according to the valid permutation
    permuted = tensor.permute(*valid_perm)

    # Make the permuted tensor contiguous to get the desired stride order
    permuted = permuted.contiguous()

    # Create the inverse permutation to get back to original dimension order
    inverse_perm = [valid_perm.index(i) for i in range(len(valid_perm))]

    # Permute back to original dimension order
    # This creates a tensor with the same shape but different strides
    result = permuted.permute(*inverse_perm)

    return result


def diff(a, b, rtol=None, atol=None,
         assert_close=True, verbose=False, title=None,
         pct_tol=None):
    """ A diff function that helps debug numerical issues
    Args:
        a: torch.Tensor
        b: torch.Tensor
        rtol: float
        atol: float
        assert_close: bool
        verbose: bool
        pct_tol: float
    Returns:
        bool: True if a and b are close, False otherwise
    """
    a = a.to(torch.float32)
    b = b.to(torch.float32)
    if rtol is None: rtol = 1e-3
    if atol is None: atol = 1e-5
    equal = torch.allclose(a, b, rtol=rtol, atol=atol)
    error_max = torch.max(torch.abs(a - b))

    pct_equal = ((((a - b).abs() <= atol + rtol * torch.abs(b)).sum().item() / a.numel()) >= pct_tol) if pct_tol is not None else False

    # Calculate absolute error
    abs_diff = torch.abs(a - b)
    total_elements = a.numel()

    # Calculate relative error where b is non-zero
    b_nonzero = b != 0
    rel_diff = torch.zeros_like(abs_diff)
    rel_diff[b_nonzero] = abs_diff[b_nonzero] / torch.abs(b[b_nonzero])
    if verbose:
        print('\n' * 3)
        print('=' * 10 + f" {title} " + '=' * 10)
        print(f"Max absolute error: {error_max.item()}")
        print(f"Tensors are {'close' if equal else 'different'} according to torch.allclose")

        # Calculate thresholds for relative error table
        rel_thresholds = torch.logspace(
         (torch.log10(torch.tensor(rtol))), 
            0.0, 
            steps=10
        )

        # Calculate thresholds for absolute error table
        abs_thresholds = torch.logspace(
         (torch.log10(torch.tensor(atol))), 
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
            flat_indices = torch.argsort(abs_diff.flatten(), descending=True)[:n_samples]
            for i in range(n_samples):
                idx = flat_indices[i]
                multi_idx = torch.unravel_index(idx, a.shape)
                multi_idx_str = ', '.join(map(str, [idx.item() for idx in multi_idx]))
                print(f"Index [{multi_idx_str}]: a={a[multi_idx].item()}, b={b[multi_idx].item()}, "
                      f"abs_diff={abs_diff[multi_idx].item()}, rel_diff={rel_diff[multi_idx].item()}")
        
        if not equal and pct_equal:
            print(f"Tensors are close for {pct_tol}% of the elements")
            equal = True

    if assert_close:
        assert equal, f"Tensors are not close! Max absolute error: {error_max.item()}"

    return equal



def test_permuted_strides_layout():
    """
    Test suite for create_permuted_strides_layout function.
    Verifies both mathematical properties and stride permutations.
    """

    def verify_strides(tensor, expected_perm):
        """Helper function to verify strides match expected relative order permutation"""
        strides = tensor.stride()
        # Get the relative order of strides
        stride_order = sorted(range(len(strides)), key=lambda i: strides[i], reverse=True)
        # Compare with expected permutation (only up to tensor dimensions)
        valid_perm = [p for p in expected_perm if p < tensor.dim()]

        return stride_order == valid_perm

    # Test 1: Basic 2D tensor permutation
    x = torch.randn(3, 4)
    y = create_permuted_strides_layout(x, [1, 0])
    assert y.shape == x.shape
    assert torch.allclose(y, x)  # Mathematical equivalence
    assert verify_strides(y, [1, 0])

    # Test 2: 3D tensor with partial permutation
    x = torch.randn(2, 3, 4)
    y = create_permuted_strides_layout(x, [2, 0, 1])
    assert y.shape == x.shape
    assert torch.allclose(y, x)
    assert verify_strides(y, [2, 0, 1])

    # Test 3: Invalid permutation indices
    x = torch.randn(2, 3)
    y = create_permuted_strides_layout(x, [0, 1, 2, 3])
    assert y.shape == x.shape
    assert torch.allclose(y, x)
    assert verify_strides(y, [0, 1])  # Only valid indices should be considered

    # Test 4: Empty permutation
    x = torch.randn(2, 3)
    y = create_permuted_strides_layout(x, [])
    assert y.shape == x.shape
    assert torch.allclose(y, x)

    # Test 5: 1D tensor
    x = torch.randn(5)
    y = create_permuted_strides_layout(x, [0])
    assert y.shape == x.shape
    assert torch.allclose(y, x)

    # Test 6: Mathematical operations
    x = torch.randn(2, 3, 4)
    y = create_permuted_strides_layout(x, [2, 0, 1])
    z = create_permuted_strides_layout(x, [1, 2, 0])

    # Test addition
    assert torch.allclose(x + y, x + x)
    assert torch.allclose(y + z, x + x)

    # Test multiplication
    assert torch.allclose(x * y, x * x)
    assert torch.allclose(y * z, x * x)

    # Test matrix multiplication (if applicable)
    if x.dim() == 2:
        assert torch.allclose(x @ y, x @ x)

    # Test 7: Different data types
    # For floating point types, use randn
    for dtype in [torch.float32, torch.float64]:
        x = torch.randn(2, 3, dtype=dtype)
        y = create_permuted_strides_layout(x, [1, 0])
        assert y.dtype == dtype
        assert torch.allclose(y, x)
        assert verify_strides(y, [1, 0])

    # For integer types, use randint
    for dtype in [torch.int32, torch.int64]:
        x = torch.randint(0, 10, (2, 3), dtype=dtype)
        y = create_permuted_strides_layout(x, [1, 0])
        assert y.dtype == dtype
        assert torch.allclose(y, x)
        assert verify_strides(y, [1, 0])

    # Test 8: Different devices
    if torch.cuda.is_available():
        x = torch.randn(2, 3, device='cuda')
        y = create_permuted_strides_layout(x, [1, 0])
        assert y.device == x.device
        assert torch.allclose(y, x)
        assert verify_strides(y, [1, 0])


if __name__ == "__main__":
    test_permuted_strides_layout()
    print("All tests passed!")