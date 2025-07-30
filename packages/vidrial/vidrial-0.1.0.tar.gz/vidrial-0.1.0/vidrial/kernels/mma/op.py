import torch as th
from vidrial.kernels.mma.binding import binding_autotuned
from vidrial.kernels.mma.dimensions import problem_shape

def canonical_inputs(A, B):
    """ Make all the arguments 3D and return a function to convert the output to the original shape """
    assert A.device == B.device, "A and B must be on the same device"
    assert A.dtype == B.dtype, "A and B must have the same dtype"
    assert A.ndim == B.ndim
    assert A.ndim in [2, 3]
    expand_batch = A.ndim == 2
    if expand_batch: A, B = A.unsqueeze(0), B.unsqueeze(0)
    problem_shape(A.shape, B.shape) # checks that the dimensions are valid
    return A, B, lambda C: C[0] if expand_batch else C

@th.library.custom_op("mosaic::mma", mutates_args=())
def op(A: th.Tensor, B: th.Tensor) -> th.Tensor:
    r"""Compute matrix multiplication: A @ B.

    Args:
        A: Input tensor of shape `(batch_size, m, k)`.
           The left matrix in the multiplication.
        B: Input tensor of shape `(batch_size, k, n)`.
           The right matrix in the multiplication.

    Returns:
        C: Output tensor of shape `(batch_size, m, n)`.
           The result of A @ B.

    Note:
        - All input tensors must be on the same device
        - All input tensors must have the same dtype
        - The batch dimension is treated as a batch dimension
        - The operation is optimized for CUDA devices
    """
    A, B, cannonical_outputs = canonical_inputs(A, B)
    P, M, N, K = problem_shape(A.shape, B.shape)
    C = th.empty(P, M, N, device=A.device, dtype=A.dtype)
    binding_autotuned(A, B, C)
    return cannonical_outputs(C)

# Make it traceable
@op.register_fake
def op_fake(A: th.Tensor, B: th.Tensor):
    A, B, cannonical_outputs = canonical_inputs(A, B)
    P, M, N, K = problem_shape(A.shape, B.shape)
    C = th.empty(P, M, N, device=A.device, dtype=A.dtype)
    return cannonical_outputs(C)


# ---------------------- Autograd --------------------------------

def op_setup(ctx, inputs, output):
    A, B = inputs
    ctx.save_for_backward(A, B)
def op_backward(ctx, dC):
    A, B = ctx.saved_tensors
    dA = op(dC, B.transpose(-1, -2))
    dB = op(A.transpose(-1, -2), dC)
    return dA, dB
th.library.register_autograd(
    "mosaic::mma", op_backward, setup_context=op_setup
)


# ---------------------- Reference --------------------------------

def op_reference(A: th.Tensor, B: th.Tensor) -> th.Tensor:
    return A @ B
