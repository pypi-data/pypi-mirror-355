from torch.utils._pytree import tree_map
from typing import Any, Callable, Optional, Union
from functools import reduce
from vidrial.jit.mosaic_types.tuples import flatten, unflatten
from vidrial.jit.mosaic_types.types import Layout
from vidrial.jit.mosaic_types.shape import Shape, shapify, static_shape
from vidrial.jit.mosaic_types.stride import Stride, strideify
from vidrial.jit.mosaic_types.int import Int, _1, _2, _3, _4, _5, _6, _7, _8, _9, _10, _16


def squeeze(thing: Shape | Stride) -> Shape | Stride:
    """Remove all singleton dimensions from a shape or stride."""
    cls = type(thing)
    if len(thing.elements) == 1 and isinstance(thing.elements[0], cls):
        return cls(squeeze(thing.elements[0])) # type: ignore
    else:
        return thing

def merge(*things: Any) -> Any:
    """Merge a list of shapes, strides, or layouts into a single shape, stride, or layout."""
    cls = type(things[0])
    assert all(isinstance(t, cls) for t in things), f"All elements must be of type {cls}"
    if len(things) == 1:
        return squeeze(things[0])
    if cls in (Shape, Stride):
        return squeeze(cls(*things))
    elif cls == Layout:
        return Layout(merge(*(t.shape for t in things)), merge(*(t.stride for t in things)))
    else:
        raise ValueError(f"Cannot merge {cls}")
    
    
def all_factors(n: int) -> list[int]:
    """Return all factors of n."""
    factors = set()
    for i in range(1, int(n**0.5) + 1):
        if n % i == 0:
            factors.add(i)
            factors.add(n // i)
    return sorted(factors)


def common_factors(a: int, b: int) -> list[int]:
    """Return the common factors of a and b."""
    return list(set(all_factors(a)) & set(all_factors(b)))


def all_divides(shape: Shape, splits: int) -> list[Shape]:
    """Return all possible shapes that can be obtained by dividing the shape into splits equal parts."""
    global indents
    if splits == 1:
        return [shape]
    if splits > shape.size():
        return []
    if shape.modes() == 1:
        return [Shape(shape.size() // splits)] if shape.size() % splits == 0 else []

    flattened, res = flatten(shape).to_list(), []
    for factor in common_factors(flattened[0], splits):
        pre_shape = [flattened[0] // factor]
        post_shapes = all_divides(Shape(*flattened[1:]), splits // factor) # type: ignore
        for post_shape in post_shapes:
            res.append(Shape(*pre_shape, *post_shape))
    for i in range(len(res)):
        res[i] = unflatten(res[i], shape)
    return res


class Get:
    def __getitem__(self, idxs: int | tuple[int, ...]) -> Callable:
        if isinstance(idxs, int):
            return lambda l: Layout(shapify(l.shape[idxs]), strideify(l.stride[idxs]))
        def get_layout(l: Layout) -> Layout:
            for idx in idxs:
                l = Get()[idx](l)
            return l
        return get_layout
    
get = Get()



def test_get_1():
    l = Layout(Shape(_1, Shape(_2, _3)), Stride(_4, Stride(_5, _6)))
    l1 = get[0](l)
    l2 = get[1, 1](l)
    assert l1.to_cpp() == "Layout<Shape<Int<1>>, Stride<Int<4>>>"
    assert l2.to_cpp() == "Layout<Shape<Int<3>>, Stride<Int<6>>>"

def test_get_2():
    l = Layout(Shape(_1, Shape(_2, Shape(_3, _4))), Stride(_4, Stride(_5, Stride(_6, _7))))
    l1 = get[1, 1](l)
    l2 = get[1, 1, 1](l)
    assert l1.to_cpp() == "Layout<Shape<Int<3>, Int<4>>, Stride<Int<6>, Int<7>>>"
    assert l2.to_cpp() == "Layout<Shape<Int<4>>, Stride<Int<7>>>"

def test_merge_shape():
    s1 = Shape(_1, _2)
    s2 = Shape(_3)
    s3 = merge(s1, s2)
    assert s3.to_cpp() == "Shape<Shape<Int<1>, Int<2>>, Int<3>>"

def test_merge_stride():
    s1 = Stride(_1, _2)
    s2 = Stride(_3)
    s3 = merge(s1, s2)
    assert s3.to_cpp() == "Stride<Stride<Int<1>, Int<2>>, Int<3>>"

def test_merge_layout_1():
    l1 = Layout(Shape(_1, _2), Stride(_3, _4))
    l2 = Layout(Shape(_5), Stride(_6))
    l3 = merge(l1, l2)
    assert l3.to_cpp() == "Layout<Shape<Shape<Int<1>, Int<2>>, Int<5>>, Stride<Stride<Int<3>, Int<4>>, Int<6>>>"

def test_merge_layout_2():
    l1 = Layout(Shape(_1, _2), Stride(_3, _4))
    l2 = Layout(Shape(_1), Stride(_2))
    l3 = merge(l1, l2)
    assert l3.to_cpp() == "Layout<Shape<Shape<Int<1>, Int<2>>, Int<1>>, Stride<Stride<Int<3>, Int<4>>, Int<2>>>"

def test_all_divides_1():
    s = Shape(_4, Shape(_4, _4), _16)
    res = all_divides(s, 2)
    assert len(res) == 4
    assert any(static_shape(r).to_cpp() == "Shape<Int<2>, Shape<Int<4>, Int<4>>, Int<16>>" for r in res)
    assert any(static_shape(r).to_cpp() == "Shape<Int<4>, Shape<Int<2>, Int<4>>, Int<16>>" for r in res)
    assert any(static_shape(r).to_cpp() == "Shape<Int<4>, Shape<Int<4>, Int<2>>, Int<16>>" for r in res)
    assert any(static_shape(r).to_cpp() == "Shape<Int<4>, Shape<Int<4>, Int<4>>, Int<8>>" for r in res)

def test_all_divides_2():
    s = Shape(_4, Shape(_4, _4), _16)
    res = all_divides(s, 8)
    assert len(res) == 17
    assert len(set(res)) == 17
    assert len(set(r.size() for r in res)) == 1
    assert any(static_shape(r).to_cpp() == "Shape<Int<1>, Shape<Int<2>, Int<4>>, Int<16>>" for r in res)
    assert any(static_shape(r).to_cpp() == "Shape<Int<1>, Shape<Int<4>, Int<2>>, Int<16>>" for r in res)
    assert any(static_shape(r).to_cpp() == "Shape<Int<1>, Shape<Int<4>, Int<4>>, Int<8>>" for r in res)
    assert any(static_shape(r).to_cpp() == "Shape<Int<2>, Shape<Int<2>, Int<2>>, Int<16>>" for r in res)
    assert any(static_shape(r).to_cpp() == "Shape<Int<2>, Shape<Int<2>, Int<4>>, Int<8>>" for r in res)
    assert any(static_shape(r).to_cpp() == "Shape<Int<2>, Shape<Int<4>, Int<2>>, Int<8>>" for r in res)
    assert any(static_shape(r).to_cpp() == "Shape<Int<4>, Shape<Int<1>, Int<2>>, Int<16>>" for r in res)
    assert any(static_shape(r).to_cpp() == "Shape<Int<4>, Shape<Int<2>, Int<1>>, Int<16>>" for r in res)
    assert any(static_shape(r).to_cpp() == "Shape<Int<4>, Shape<Int<2>, Int<2>>, Int<8>>" for r in res)
    assert any(static_shape(r).to_cpp() == "Shape<Int<4>, Shape<Int<4>, Int<1>>, Int<8>>" for r in res)
    assert any(static_shape(r).to_cpp() == "Shape<Int<4>, Shape<Int<1>, Int<4>>, Int<8>>" for r in res)
    assert any(static_shape(r).to_cpp() == "Shape<Int<4>, Shape<Int<2>, Int<4>>, Int<4>>" for r in res)
    assert any(static_shape(r).to_cpp() == "Shape<Int<4>, Shape<Int<4>, Int<2>>, Int<4>>" for r in res)
    assert any(static_shape(r).to_cpp() == "Shape<Int<4>, Shape<Int<4>, Int<4>>, Int<2>>" for r in res)
