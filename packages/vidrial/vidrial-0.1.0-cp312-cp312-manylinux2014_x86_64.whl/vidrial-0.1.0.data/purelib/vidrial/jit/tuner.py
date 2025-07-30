from typing import Callable, Any, Iterable
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import inspect
import time
import random
import logging
from vidrial.jit.timingcache import ConfigTimingCache
from vidrial.jit.timer import timeit

logger = logging.getLogger(__name__)

def get_fn_name(fn: Callable) -> str:
    return f"{fn.__module__}.{fn.__qualname__}".replace("<locals>.", "")

def parallel_warmup(fn: Callable,
                    args: dict,
                    configs: list[dict],
                    allow_failure: bool,
                    max_workers: int,
                    verbose: bool,
                    name: str | None = None) -> list[dict]:
    """
    Warmup a given function in parallel (i.e., call it once for each config). The keys of `args_dict`
    and the keys of each config together must completely specify the arguments of the function.

    :param fn: The function to warmup.
    :param args: A dictionary of "fixed" arguments to the function
    :param configs: A list of dictionaries of containing additional arguments to the function.
    :param allow_failure: If True, the tuner will not raise an error if at least one of the configurations succeeds to run.
    :param max_workers: The maximum number of workers to use for the warmup.
    :param verbose: If True, the tuner will print progress information.
    :param name: optional name of the kernel to be used for logging.

    :return: A list of configurations that succeeded to run.
    """
    def _run(config):
        fn(*args.values(), **config)
        return config

    fn_name = name or get_fn_name(fn)
    
    errors, success_configs, start_time = [], [], time.time()
    with ThreadPoolExecutor(max_workers=min(max_workers, len(configs))) as executor:
        futures = [executor.submit(_run, config) for config in configs]
        with tqdm(total=len(configs), desc=f"Warming up for {fn_name}", disable=not verbose) as pbar:
            for future in as_completed(futures):
                try:
                    config = future.result()
                    success_configs.append(config)
                except Exception as e:
                    logger.debug(f"Error during warmup: {e}")
                    errors.append(str(e))
                pbar.update(1)
    print(f"{len(success_configs)=}, {len(configs)=}, {allow_failure=}")
    if len(success_configs) < len(configs) and ((not allow_failure) or len(success_configs) == 0):
        error_msg = f"{len(configs) - len(success_configs)} out of {len(configs)} warmup runs failed for {fn_name}:\n"
        for i, err in enumerate(errors):
            error_msg += f"- Config {i}: {err}\n"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    logger.debug(f"Warmup completed for {fn_name}: {len(success_configs)} successful, {len(errors)} failed in {time.time() - start_time:.2f} seconds")
    return success_configs


def kerneltune(
    fn: Callable,
    args: dict,
    configs: list[dict] | Callable, # type: ignore
    num: int = 10,
    max_workers: int = 8,
    no_side_effect: bool = True,
    verbose: bool = False,
    allow_failure: bool = True,
    name: str | None = None):
    """
    Tunes a kernel by test-running different configurations, returns timing results in the following format:
    [
        {
            "config": {...}, # The configuration that was tested
            "time": float,   # Average time of the run
            "std": float,    # Standard deviation of the time
            "n": int,        # Number of runs incurred
        },
        ...
    ]

    Example:
        def add_one_kernel(X, Y, d0_tile, d1_tile, thread_num):
            runtime = jit(...)
            runtime(X, Y)
            return Y

        timings = kerneltune(
            fn=add_one_kernel,
            args={'X': X, 'Y': Y},
            configs=[
                {'d0_tile': 16, 'd1_tile': 16, 'thread_num': 16},
                {'d0_tile': 32, 'd1_tile': 32, 'thread_num': 32},
                {'d0_tile': 64, 'd1_tile': 64, 'thread_num': 64},
            ],
            no_side_effects=True,
        )


    :note: When all the configurations are evaluated, the kernel will run multiple times. This means that whatever value the kernel updates will be updated multiple times. To avoid this undesired behavior, you can use the `reset_to_zero` argument, which resets the value of the provided tensor to `zero` before running any configuration.
        
    :note: Unlike triton.autotune, we use standard nvcc compilation tool chain to compile the kernel. This means that we'll spin up multiple processes to compile the kernels for different configurations first before benchmarking.

    :param fn: the runnable to tune
    :param configs: List of config dictionaries, or functions that return a list of config dictionaries
    :param num: number of times to run the kernel for each configuration
    :param max_workers: number of workers to use for the warmup
    :param no_side_effect: if True, the tuner will restore the values of the provided argument names after evaluating any configs.
    :param verbose: if True, the tuner will print progress information.
    :param allow_failure: if True, the tuner will not raise an error if at least one of the configurations succeeds to run.
    :param name: optional name of the kernel to be used for logging.
    """
    assert num >= 3, "num must be at least 3"
    num1 = num // 3
    num2 = num - num1
    fn_name = name or get_fn_name(fn)

    def _bench(config: dict) -> dict:
        args_copy = {name: args[name].detach().clone() if hasattr(args[name], "detach") else args[name] for name in args} if no_side_effect else args
        avg_time, std_time = timeit(lambda: fn(*args_copy.values(), **config), num1=num1, num2=num2)
        logger.debug(f"Time for {fn_name} with config {config}: {avg_time:.2f} ± {std_time:.2f} seconds")
        return {'config': config, 'time': avg_time, 'std': std_time, 'n': num1 + num2}

    if isinstance(configs, Callable):
        configs: list[dict] = configs(args.values())
    else:
        configs = configs
    bench_start = time.time()
    if max_workers > 1:
        configs = parallel_warmup(fn, args, configs, allow_failure, max_workers, verbose, fn_name)
    timings = [_bench(config=config) for config in (tqdm(configs, desc="Benchmarking") if verbose else configs)]
    bench_end = time.time()
    bench_time = bench_end - bench_start
    logger.debug(f"Tuning time for {fn_name}: {bench_time:.2f} seconds")
    timings = sorted(timings, key=lambda x: x['time'])
    config = timings[0]['config']
    logger.debug(f"Best config for {fn_name}: {config}")
    return timings
    

def tune_and_update(fn: Callable,
                    args: Iterable[Any],
                    configs: list[dict] | Callable,
                    cache: ConfigTimingCache,
                    num: int = 10,
                    max_workers: int = 8,
                    no_side_effect: bool = True,
                    verbose: bool = False,
                    allow_failure: bool = True) -> list[dict]:
    """ Tunes a function and updates the function with the collected timings.
    """
    if not isinstance(args, dict):
        arg_names = list(inspect.signature(fn).parameters.keys())
        args = dict(zip(arg_names, args))
    timings = kerneltune(fn, args, configs, num, max_workers, no_side_effect, verbose, allow_failure)
    cache.update(args, timings)
    return timings

def sample_configs(configs: list[dict], n: int = 10) -> list[dict]:
    """Sample a random subset of the configurations.
    """
    random.seed(42)
    return random.sample(configs, min(n, len(configs)))