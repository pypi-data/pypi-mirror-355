from typing import Any, Union, Iterator, Iterable
from torch.utils._pytree import register_pytree_node
from vidrial.jit.mosaic_types.int import Int, BaseType
from functools import reduce

class Tuple(BaseType):
    """Represents a hierarchical integer tuple type. A tuple can be constructed
    from a (mixed) list of ints, tuples, or Ints, but once constructed,
    all elements are either Ints or Tuples."""
    elements: tuple[Union[Int, 'Tuple', int], ...]
    name: str = "Tuple"

    def __init__(self, *elements: Union[int, 'Tuple', Int]):
        assert all(isinstance(elem, (Int, Tuple, int, tuple)) for elem in elements), f"elements={elements} should be a list of Ints or Tuples"
        _elements = []
        for elem in elements:
            if isinstance(elem, tuple):
                _elements.append(self.__class__(*elem))
            else:
                _elements.append(elem)
        self.elements = tuple(_elements)

    def __getitem__(self, idx: Union[int, slice]) -> Union['Tuple', Int, int]:
        if isinstance(idx, int):
            return self.elements[idx]
        elif isinstance(idx, slice):
            return self.__class__(*self.elements[idx])
        else:
            raise ValueError(f"Invalid index type: {type(idx)}")

    def __iter__(self) -> Iterator[Union['Tuple', Int, int]]:
        return iter(self.elements)
    
    def to_cpp(self, enclosed: bool = False) -> str:
        elements_str = ", ".join(elem.to_cpp(True) if isinstance(elem, BaseType) else str(elem) for elem in self.elements)
        if enclosed and len(self.elements) == 1:
            return elements_str
        return f"{self.name}<{elements_str}>"
    
    def size(self) -> int:
        return reduce(lambda x, y: x * (y.size() if isinstance(y, BaseType) else y), self.elements, 1)
    
    def rank(self) -> int:
        return len(self.elements)
    
    def depth(self) -> int:
        return max(elem.depth() + 1 if isinstance(elem, self.__class__) else 1 for elem in self.elements)
    
    def modes(self) -> int:
        return sum(elem.modes() if isinstance(elem, self.__class__) else 1 for elem in self.elements)
    
    def to_tuple(self) -> tuple[Any, ...]:
        """Convert a Tuple to a python tuple containing python ints or tuples of ints."""
        return tuple(elem.to_tuple() if isinstance(elem, self.__class__) else elem for elem in self.elements)
    
    def to_list(self) -> list[Any]:
        """Convert a Tuple to a python list containing python ints or tuples of ints."""
        return [elem.to_list() if isinstance(elem, self.__class__) else elem for elem in self.elements]

    def __hash__(self) -> int:
        return hash(self.to_tuple())

    def __str__(self) -> str:
        if len(self.elements) == 1:
            if isinstance(self.elements[0], Int):
                return str(self.elements[0])
            else:
                return f"({','.join(str(elem) for elem in self.elements)})"
        else:
            return f"({','.join(str(elem) for elem in self.elements)})"
        
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(elements={', '.join(repr(elem) for elem in self.elements)})"
    
    def __len__(self) -> int:
        return len(self.elements)
    
    def __contains__(self, item: Any) -> bool:
        return item in self.elements
    
    def __eq__(self, other: 'Tuple') -> bool:
        if not isinstance(other, self.__class__):
            return False
        if len(self.elements) != len(other.elements):
            return False
        return all(elem == other.elements[i] for i, elem in enumerate(self.elements)) # type: ignore
    
    def __reduce__(self):
        """Make Tuple picklable by specifying how to reconstruct it."""
        return (type(self), self.elements)


def flatten(tup: Tuple) -> Tuple:
    """Recursively flatten a tuple of tup."""
    flattened = []
    cls = type(tup)
    for item in tup:
        if isinstance(item, Tuple):
            flattened.extend(flatten(item))
        else:
            flattened.append(item)
    return cls(*flattened)


def unflatten(flat: Iterable[Any], target: Tuple) -> Tuple:
    """Unflatten a flat tuple into a the structure of the target tuple."""
    flat = list(flat)
    assert len(flat) == len(flatten(target)), f"flat={flat} and target={target} must have the same number of elements"
    res = []
    cls = type(target)
    for item in target:
        if isinstance(item, (Int, int)):
            res.append(flat[0])
            flat = flat[1:] # type: ignore
        elif isinstance(item, Tuple):
            res.append(unflatten(flat[:item.modes()], item)) # type: ignore
            flat = flat[item.modes():] # type: ignore
    return cls(*res)
        

register_pytree_node(Tuple, lambda t: (list(flatten(t)), t), unflatten)
