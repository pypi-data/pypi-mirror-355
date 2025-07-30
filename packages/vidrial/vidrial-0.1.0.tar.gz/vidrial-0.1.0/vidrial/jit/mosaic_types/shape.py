from torch.utils._pytree import register_pytree_node
from vidrial.jit.mosaic_types.int import Int
from vidrial.jit.mosaic_types.tuples import Tuple, flatten, unflatten

class Shape(Tuple):
    """Represents a shape type with nested dimensions. A shape can be constructed
    from a (mixed) list of ints, shapes, or Ints, but once constructed, all elements
    are either Ints or Shapes."""
    name = "Shape"


def shapify(shape: Shape | Int) -> Shape:
    if isinstance(shape, Int):
        return Shape(shape)
    return shape

def static_shape(t) -> Shape:
    if isinstance(t, tuple) or isinstance(t, list) or isinstance(t, Shape):
        return Shape(*[static_shape(i) for i in t])
    if isinstance(t, int):
        return Shape(Int(t))
    if isinstance(t, Int):
        return Shape(t)
    raise ValueError(f"Invalid shape type: {type(t)}")


register_pytree_node(Shape, lambda t: (list(flatten(t)), t), unflatten)