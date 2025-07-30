import inspect
import copy
import os
from typing import Callable, Any
from functools import wraps
from vidrial.jit.tuner import tune_and_update
from vidrial.jit.timingcache import ConfigTimingCache
from vidrial.jit.package import register_config_cache
import logging

logger = logging.getLogger(__name__)


def pickbest(cache: ConfigTimingCache,
             sweep: list[dict] | Callable | None = None,
             max_workers: int | None = None,
             allow_failure: bool = True,
             verbose: bool = False) -> Callable:
    """ Decorator for picking the best configuration from a config cache object when running a 
    function, optionally run a sweep of configurations to pick the best one when cache misses. 
    

    Canonical usage:
    ```python
        cache = ConfigTimingCache('fn', lambda args: args['X'].shape)
        def sweep(args: dict) -> list[dict]:
            return [
                {'tile_1': 32, 'tile_2': 32, 'thread_num': 32},
                {'tile_1': 64, 'tile_2': 64, 'thread_num': 64},
            ]

        @pickbest(cache, sweep=sweep)
        def fn(X, Y, tile_1, tile_2, thread_num) -> torch.Tensor:
            ...

        fn(X, Y)
    ```
    where the best configuration is picked from the set of configurations that are provided by the decorator.

    There are 3 places where the the configuration can be picked from:
    1. TuningCache: If a given set of argument hashes to a key that is in the cache, the best configuration is picked from the cache.
    2. Sweeping: If cache misses and a sweep is provided, the decorator will run a sweep of configurations and pick the best one (and optionally update the cache).
    3. Default Kwargs: If the function's kwargs with default values is a complete specification of configuration, the decorator will use the default values to run the function as a last resort.

    It is also possible to bypass the decorator entirely by calling the function with a complete specification of configuration.

    The above semantics are exemplified below:
    
    ```python
        @pickbest(cache)
        def fn(X: torch.Tensor, Y: torch.Tensor, tile_1: int, tile_2: int, thread_num: int) -> torch.Tensor:
            ...

        fn(X, Y) // rely on TuningCache, fails if no cache is found
    ```

    ```python
        @pickbest(cache, sweep=sweep)
        def fn(X: torch.Tensor, Y: torch.Tensor, tile_1: int, tile_2: int, thread_num: int) -> torch.Tensor:
            ...

        fn(X, Y) // rely on TuningCache first, then sweep if cache misses
    ```

    ```python
        @pickbest(cache)
        def fn(X: torch.Tensor, Y: torch.Tensor, tile_1: int = 32, tile_2: int = 32, thread_num: int = 32) -> torch.Tensor:
            ...

        fn(X, Y) // rely on TuningCache first, then default kwargs if cache misses
    ```

    ```python
        @pickbest(cache, sweep=sweep)
        def fn(X: torch.Tensor, Y: torch.Tensor, tile_1, tile_2, thread_num) -> torch.Tensor:
            ...

        fn(X, Y, tile_1=32, tile_2=32, thread_num=32) // bypass the decorator entirely
    ```

    Args:
        cache: A ConfigTimingCache object to store the cache.
        sweep: A list of configurations or a function that takes the arguments and returns a list of configurations to use if the cache is missed.
        max_workers: The maximum number of workers to use for tuning. Default to half of CPUs available.
        allow_failure: Whether to allow the function to fail. If True, the function will be retried with a different configuration.
        verbose: Whether to print verbose output.

    Returns:
        A decorator that wraps the function and returns the best configuration.
    """
    assert cache is not None, "cache must be provided"
    register_config_cache(cache)
    if max_workers is None:
        max_workers = max(1, (os.cpu_count() or 16) // 2)

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def _wrapped(*args, **kwargs) -> Any:
            nonlocal max_workers
            default_kwargs = {k: v.default for k, v in inspect.signature(fn).parameters.items() if v.default is not inspect.Parameter.empty}
            all_arg_names = list(inspect.signature(fn).parameters.keys())
            _args = dict(zip(all_arg_names, args)) | kwargs

            if len(_args) == len(all_arg_names): # bypass the decorator
                return fn(**_args)

            if _args in cache: # rely on TuningCache
                logger.debug(f"Cache hit for {cache.fn}")
                best_config = cache[_args]
                return fn(**_args, **best_config)
            elif sweep is not None: # live tuning
                configs = sweep(_args) if callable(sweep) else copy.copy(sweep)
                max_workers = min(max_workers, len(configs)) # type: ignore
                logger.debug(f"Cache miss for {cache.fn}, live tuning with {len(configs)} configs and {max_workers} workers")
                if isinstance(configs, list) and len(configs) > 1:
                    timings = tune_and_update(fn, _args, configs, cache, num=10, allow_failure=allow_failure, no_side_effect=True, max_workers=max_workers, verbose=verbose)
                    best_config = timings[0]['config']
                elif isinstance(configs, list) and len(configs) == 1:
                    best_config = configs[0]
                elif isinstance(configs, dict):
                    best_config = configs
                else:
                    raise ValueError("Cache miss and no valid configs are provided")
                return fn(**_args, **best_config)
            else: # rely on default kwargs as last resort
                all_args = {**_args, **default_kwargs}
                if set(all_args.keys()) == set(all_arg_names):
                    return fn(**all_args)
                else:
                    raise ValueError("Cache miss and no configs can be found")
        
        return _wrapped
    
    return decorator
