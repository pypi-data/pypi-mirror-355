import pytest
import yaml
import pickle
from functools import reduce
from torch.utils._pytree import tree_map, tree_flatten
from vidrial.jit.mosaic_types import Tuple, Int

EXAMPLES = [
    (2,),
    (Int(2),),
    (1, 2, 3),
    (1, (2, 3)),
    (1, (2, (3, 4))),
    (1, (2, (3, (4, 5)))),
    (1, (Int(2), (3, (4, 5)))),
    (1, (Int(2), (3, Tuple(4, 5)))),
]



@pytest.mark.parametrize("example", EXAMPLES, ids=str)
def test_rank(example):
    t = Tuple(*example)
    assert t.rank() == len(example)


@pytest.mark.parametrize("example", EXAMPLES, ids=str)
def test_size(example):
    t = Tuple(*example)
    t_flat, _ = tree_flatten(tree_map(lambda x: int(x), t))
    assert t.size() == reduce(lambda x, y: x * y, t_flat, 1)


@pytest.mark.parametrize("example", EXAMPLES, ids=str)
def test_depth(example):
    t = Tuple(*example)
    def _depth(tup: tuple | Tuple) -> int:
        return max(1 + _depth(x) if isinstance(x, (tuple, Tuple)) else 1 for x in tup)
    assert t.depth() == _depth(example)


@pytest.mark.parametrize("example", EXAMPLES, ids=str)
def test_modes(example):
    t = Tuple(*example)
    def _modes(tup: tuple | Tuple) -> int:
        return sum(_modes(x) if isinstance(x, (tuple, Tuple)) else 1 for x in tup)
    assert t.modes() == _modes(example)


@pytest.mark.parametrize("example", EXAMPLES, ids=str)
def test_to_tuple(example):
    t = Tuple(*example)
    def _to_tuple(tup: tuple | Tuple) -> tuple:
        return tuple(_to_tuple(x) if isinstance(x, (tuple, Tuple)) else x for x in tup)
    assert _to_tuple(t) == _to_tuple(example)


@pytest.mark.parametrize("example", EXAMPLES, ids=str)
def test_to_list(example):
    t = Tuple(*example)
    def _to_list(tup: tuple | Tuple) -> list:
        return [_to_list(x) if isinstance(x, (tuple, Tuple)) else x for x in tup]
    assert t.to_list() == _to_list(example)


@pytest.mark.parametrize("example", EXAMPLES, ids=str)
def test_iter(example):
    t = Tuple(*example)
    def _check_iter(tup: tuple | Tuple, example: tuple) -> bool:
        for x, y in zip(tup, example):
            if isinstance(x, (tuple, Tuple)):
                return _check_iter(x, y)
            else:
                assert x == y
        return True
    assert _check_iter(t, example)


@pytest.mark.parametrize("example", EXAMPLES, ids=str)
def test_eq(example):
    t1 = Tuple(*example)
    t2 = Tuple(*example)
    assert t1 == t2
    assert t1 != Tuple(*(example[1:]))
    assert t1 != Tuple(*(example[:-1]))
    assert t1 != Tuple(*(example[1:] + example[:-1]))
    assert t1 != Tuple(*(example[1:] + example[:-1]))


@pytest.mark.parametrize("example", EXAMPLES, ids=str)
def test_pickle(example):
    t = Tuple(*example)
    t_pickled = pickle.dumps(t)
    t_unpickled = pickle.loads(t_pickled)
    assert t == t_unpickled


@pytest.mark.parametrize("example", EXAMPLES, ids=str)
def test_yaml(example):
    t = Tuple(*example)
    assert yaml.load(yaml.dump(t), yaml.Loader) == t