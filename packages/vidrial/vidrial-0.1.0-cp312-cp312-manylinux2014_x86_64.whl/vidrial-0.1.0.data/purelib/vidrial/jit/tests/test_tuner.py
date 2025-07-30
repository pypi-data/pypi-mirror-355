import torch
from vidrial.jit.tuner import kerneltune, tune_and_update, get_fn_name
from vidrial.jit.timingcache import ConfigTimingCache


def test_tuner(add_one_kernel):
    X = torch.randn(1024, 1024, device="cuda")
    Y = torch.empty_like(X)
    timeings = kerneltune(
        add_one_kernel,
        {'X': X, 'Y': Y},
        configs=[{'d0_tile': 16, 'd1_tile': 16, 'thread_num': 32}, {'d0_tile': 32, 'd1_tile': 32, 'thread_num': 32}, {'d0_tile': 64, 'd1_tile': 64, 'thread_num': 64}],
        num=10,
        no_side_effect=True)
    assert len(timeings) == 3
    assert any(timing['config'] == {'d0_tile': 16, 'd1_tile': 16, 'thread_num': 32} for timing in timeings)
    assert any(timing['config'] == {'d0_tile': 32, 'd1_tile': 32, 'thread_num': 32} for timing in timeings)
    assert any(timing['config'] == {'d0_tile': 64, 'd1_tile': 64, 'thread_num': 64} for timing in timeings)
    assert all(timing['n'] == 10 for timing in timeings)
    assert all(timing['std'] > 0. for timing in timeings)
    # assert all(timing['time'] > 0. for timing in timeings)

def test_tuner_allow_failure(add_one_kernel):
    X = torch.randn(1024, 1024, device="cuda")
    Y = torch.empty_like(X)
    timeings = kerneltune(
        add_one_kernel,
        {'X': X, 'Y': Y},
        configs=[{'d0_tile': 16, 'd1_tile': 16, 'thread_num': 32}, {'d0_tile': 32, 'd1_tile': 32, 'thread_num': 32}, {'d0_tile': 64, 'd1_tile': 64, 'thread_num': 19999}],
        num=10,
        no_side_effect=True,
        allow_failure=True)
    assert len(timeings) == 2
    assert any(timing['config'] == {'d0_tile': 16, 'd1_tile': 16, 'thread_num': 32} for timing in timeings)
    assert any(timing['config'] == {'d0_tile': 32, 'd1_tile': 32, 'thread_num': 32} for timing in timeings)
    assert all(timing['n'] == 10 for timing in timeings)
    assert all(timing['std'] > 0. for timing in timeings)
    # assert all(timing['time'] > 0. for timing in timeings)

def test_tune_and_update(add_one_kernel, tmp_path):
    X = torch.randn(1024, 1024, device="cuda")
    Y = torch.empty_like(X)
    hash_fn = lambda args: str(tuple(args['X'].shape) + tuple(args['X'].stride()))
    cache = ConfigTimingCache(get_fn_name(add_one_kernel), hash_fn, root=str(tmp_path))
    configs = [{'d0_tile': 16, 'd1_tile': 16, 'thread_num': 32}, {'d0_tile': 32, 'd1_tile': 32, 'thread_num': 32}, {'d0_tile': 64, 'd1_tile': 64, 'thread_num': 64}]
    timeings = tune_and_update(
        add_one_kernel,
        {'X': X, 'Y': Y},
        configs=configs,
        cache=cache,
        num=10,
        no_side_effect=True)
    assert len(timeings) == 3
    assert any(timing['config'] == {'d0_tile': 16, 'd1_tile': 16, 'thread_num': 32} for timing in timeings)
    assert any(timing['config'] == {'d0_tile': 32, 'd1_tile': 32, 'thread_num': 32} for timing in timeings)
    assert any(timing['config'] == {'d0_tile': 64, 'd1_tile': 64, 'thread_num': 64} for timing in timeings)
    assert all(timing['n'] == 10 for timing in timeings)
    assert all(timing['std'] > 0. for timing in timeings)
    # assert all(timing['time'] > 0. for timing in timeings)

    # check the cache
    args = {'X': X, 'Y': Y}
    assert len(cache) == 1
    assert args in cache
    assert any(cache[args] == config for config in configs)


