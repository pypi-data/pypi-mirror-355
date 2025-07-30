import torch
import math

def wrap_with_timer(fn, n=10, warmup=3):
    """Takes a function and returns a function that calls it n times and returns the total time."""
    def timed_fn(*args, **kwargs):
        torch.cuda.synchronize()
        for _ in range(warmup):
            fn(*args, **kwargs)

        cache = torch.empty(int(256e6), dtype=torch.int8, device='cuda')
        def flush_cache():
            cache.zero_()
        torch.cuda.synchronize()

        start_events = [torch.cuda.Event(enable_timing=True) for _ in range(n)]
        end_events = [torch.cuda.Event(enable_timing=True) for _ in range(n)]
        for i in range(n):
            flush_cache()
            torch.cuda._sleep(1_000_000)
            start_events[i].record() # type: ignore
            out = fn(*args, **kwargs)
            end_events[i].record() # type: ignore
        torch.cuda.synchronize()
        times = [s.elapsed_time(e) for s, e in zip(start_events, end_events)]
        total_time = sum(times)
        std = math.sqrt(sum((t - total_time / n) ** 2 for t in times) / n)
        return out, total_time, std
    return timed_fn


def timeit(fn, *args, num1=10, num2=50, **kwargs):
    """Takes a function and returns a an estimate of time per iteration."""
    timed_fn_1 = wrap_with_timer(fn, num1)
    timed_fn_2 = wrap_with_timer(fn, num2)

    _, t1, std1 = timed_fn_1(*args, **kwargs)
    _, t2, std2 = timed_fn_2(*args, **kwargs)

    return (t2 - t1) / (num2 - num1), math.sqrt((num1 * std1**2 + num2 * std2**2) / (num1 + num2))