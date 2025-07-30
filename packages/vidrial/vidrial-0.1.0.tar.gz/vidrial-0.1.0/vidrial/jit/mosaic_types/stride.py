from torch.utils._pytree import register_pytree_node
from vidrial.jit.mosaic_types.int import Int
from vidrial.jit.mosaic_types.tuples import Tuple, flatten, unflatten

class Stride(Tuple):
    """Represents a stride type, similar to Shape but for strides. A stride can be
    constructed from a (mixed) list of ints, strides, or Ints, but once constructed,
    all elements are either Ints or Strides."""
    name = "Stride"


def strideify(stride: Stride | Int) -> Stride:
    if isinstance(stride, Int):
        return Stride(stride)
    return stride


register_pytree_node(Stride, lambda t: (list(flatten(t)), t), unflatten)