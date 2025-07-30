import torch
from unittest.mock import patch, Mock, MagicMock
from vidrial.jit.decorator import pickbest, tune_and_update
from vidrial.jit.tuner import get_fn_name
from vidrial.jit.timingcache import ConfigTimingCache
from vidrial.jit.compiler import compile

def test_pickbest_cache_miss_and_tune(add_one_kernel, tmp_path):
    with patch('vidrial.jit.decorator.tune_and_update', wraps=tune_and_update) as mock_tune_and_update:
        @pickbest(
            cache=ConfigTimingCache(get_fn_name(add_one_kernel), lambda args: str(tuple(args['X'].shape) + tuple(args['X'].stride())), root=str(tmp_path)),
            sweep=[
                {'d0_tile': 16, 'd1_tile': 16, 'thread_num': 32},
                {'d0_tile': 32, 'd1_tile': 32, 'thread_num': 32},
                {'d0_tile': 64, 'd1_tile': 64, 'thread_num': 64}],
            )
        def add_one(X, Y, d0_tile, d1_tile, thread_num):
            return add_one_kernel(X, Y, d0_tile, d1_tile, thread_num)
        
        X = torch.randn(64, 64, device="cuda")
        Y = torch.empty_like(X)

        # call once, should tune since no cache
        add_one(X, Y) # type: ignore
        assert mock_tune_and_update.call_count == 1
        torch.testing.assert_close(X + 1, Y)

        # call again, should have cache hit
        mock_tune_and_update.reset_mock()
        add_one(X, Y) # type: ignore
        assert mock_tune_and_update.call_count == 0
        torch.testing.assert_close(X + 1, Y)


def test_pickbest_cache_miss_and_heuristic(add_one_kernel, tmp_path):
    with patch('vidrial.jit.decorator.tune_and_update', wraps=tune_and_update) as mock_tune_and_update:
        def _fallback_heuristic(args):
            return {
                'd0_tile': 32 if args['X'].shape[0] % 32 == 0 else 16,
                'd1_tile': 32 if args['X'].shape[1] % 32 == 0 else 16,
                'thread_num': 32
            }
        
        mock_heuristic = Mock(side_effect=_fallback_heuristic)

        @pickbest(
            cache=ConfigTimingCache(get_fn_name(add_one_kernel), lambda args: str(tuple(args['X'].shape) + tuple(args['X'].stride())), root=str(tmp_path)),
            sweep=mock_heuristic)
        def add_one(X, Y, d0_tile, d1_tile, thread_num):
            return add_one_kernel(X, Y, d0_tile, d1_tile, thread_num)
        
        X = torch.randn(64, 64, device="cuda")
        Y = torch.empty_like(X)

        add_one(X, Y) # type: ignore
        # should not tune but make a call to the heuristic
        assert mock_tune_and_update.call_count == 0
        mock_heuristic.assert_called_once()
        torch.testing.assert_close(X + 1, Y)

        # call again, should still rely on the heuristic
        mock_tune_and_update.reset_mock()
        mock_heuristic.reset_mock()
        add_one(X, Y) # type: ignore
        assert mock_tune_and_update.call_count == 0
        mock_heuristic.assert_called_once()
        torch.testing.assert_close(X + 1, Y)


def test_pickbest_bypass(add_one_kernel, tmp_path):
    mock_cache = MagicMock()
    mock_cache.__contains__.return_value = False
    with patch('vidrial.jit.decorator.tune_and_update', wraps=tune_and_update) as mock_tune_and_update:
        @pickbest(
            cache=mock_cache,
            sweep=[
                {'d0_tile': 16, 'd1_tile': 16, 'thread_num': 32},
                {'d0_tile': 32, 'd1_tile': 32, 'thread_num': 32},
                {'d0_tile': 64, 'd1_tile': 64, 'thread_num': 64}],
            )
        def add_one(X, Y, d0_tile, d1_tile, thread_num):
            return add_one_kernel(X, Y, d0_tile, d1_tile, thread_num)
    
        X = torch.randn(64, 64, device="cuda")
        Y = torch.empty_like(X)

        add_one(X, Y) # type: ignore
        assert mock_cache.__contains__.call_count == 1
        assert mock_tune_and_update.call_count == 1
        torch.testing.assert_close(X + 1, Y)
        
        # call again with all config args provided, should bypass the decorator
        mock_cache.reset_mock()
        mock_tune_and_update.reset_mock()
        add_one(X, Y, 16, 16, 32) # type: ignore
        assert mock_cache.__contains__.call_count == 0
        assert mock_tune_and_update.call_count == 0
        torch.testing.assert_close(X + 1, Y)


def test_pickbest_kwargs_last_resort(add_one_kernel, tmp_path):
    @pickbest(
        cache=ConfigTimingCache(get_fn_name(add_one_kernel), lambda args: str(tuple(args['X'].shape) + tuple(args['X'].stride())), root=str(tmp_path)),
        sweep=[
            {'d0_tile': 16, 'd1_tile': 16, 'thread_num': 32},
            {'d0_tile': 32, 'd1_tile': 32, 'thread_num': 32},
            {'d0_tile': 64, 'd1_tile': 64, 'thread_num': 64}],
        )
    def add_one(X, Y, d0_tile=16, d1_tile=16, thread_num=32):
        return add_one_kernel(X, Y, d0_tile, d1_tile, thread_num)
    
    X = torch.randn(64, 64, device="cuda")
    Y = torch.empty_like(X)

    with patch('vidrial.jit.jit.compile', wraps=compile) as mock_compile:
        # call once, will populate cache by compiling all configs
        add_one(X, Y) # type: ignore
        assert mock_compile.call_count == 3
        torch.testing.assert_close(X + 1, Y)

        # call again, should not compile since cache is hit
        mock_compile.reset_mock()
        add_one(X, Y) # type: ignore
        assert mock_compile.call_count == 0
        torch.testing.assert_close(X + 1, Y)

        # call again with all config args provided, should bypass the decorator, so compile once
        # for the new config
        mock_compile.reset_mock()
        add_one(X, Y, 16, 32, 32) # type: ignore
        assert mock_compile.call_count == 1
        torch.testing.assert_close(X + 1, Y)
    
    
    