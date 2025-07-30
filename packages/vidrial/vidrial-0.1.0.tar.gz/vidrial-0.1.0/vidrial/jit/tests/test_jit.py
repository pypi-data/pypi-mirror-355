import torch
from unittest.mock import patch
from vidrial.jit.jit import jit, parallel_jit
from vidrial.jit.compiler import compile


def test_jit(get_add_one_kernel_code, tmp_path):
    with patch('vidrial.jit.jit.compile', wraps=compile) as mock_compile:
        X = torch.randn(64, 64, device="cuda")
        Y = torch.empty_like(X)
        code = get_add_one_kernel_code(X, Y)
        runtime = jit("test_add_one_kernel", code, root=str(tmp_path))
        runtime(X, Y)
        torch.testing.assert_close(X + 1, Y)
        mock_compile.assert_called_once()

        # Now call it second time, it should be cached
        mock_compile.reset_mock()
        runtime = jit("test_add_one_kernel", code, root=str(tmp_path))
        runtime(X, Y)
        assert mock_compile.call_count == 0


def test_parallel_jit(get_add_one_kernel_code, tmp_path):
    with patch('vidrial.jit.jit.compile', wraps=compile) as mock_compile:
        jobs = []
        for tile in [16, 32, 64]:
            X = torch.randn(64, 64, device="cuda")
            Y = torch.empty_like(X)
            code = get_add_one_kernel_code(X, Y, tile_d0=tile, tile_d1=tile, thread_num=32)
            jobs.append(("test_add_one_kernel", code, None, None, str(tmp_path), None))
        runtimes = parallel_jit(jobs, max_workers=3, verbose=True)
        assert mock_compile.call_count == 3
        for runtime in runtimes:
            X = torch.randn(64, 64, device="cuda")
            Y = torch.empty_like(X)
            runtime(X, Y)
            torch.testing.assert_close(X + 1, Y)

        # Now call it second time, it should be cached
        mock_compile.reset_mock()
        runtimes = parallel_jit(jobs, max_workers=3, verbose=True)
        assert mock_compile.call_count == 0
        for runtime in runtimes:
            X = torch.randn(64, 64, device="cuda")
            Y = torch.empty_like(X)
            runtime(X, Y)
            torch.testing.assert_close(X + 1, Y)