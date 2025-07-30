import concurrent.futures
import copy
from typing import Optional, Any
from vidrial.jit.compiler import compile, compiler_flags, get_kernel_hash, hash_to_hex, get_nvcc_compiler, DEFAULT_INCLUDE_DIRS
from vidrial.jit.runtime import Runtime
from vidrial.jit.package import register_runtime
from tqdm import tqdm
import os
import logging

logger = logging.getLogger(__name__)
DEFAULT_JIT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.jit_cache')


def build_path(name: str, code: str, root: str, flags: list[str] = []):
    signature = f'{name}$${get_kernel_hash(code)}$${code}$${get_nvcc_compiler()}$${flags}'
    name = f'kernel.{name}.{hash_to_hex(signature)}'
    return f'{root}/{name}'


def render(template: str, template_params: dict[str, Any]) -> str:
    """Format a C++ template string with the given template parameters.
    
    Args:
        template: The template string with {key} placeholders
        template_params: Dictionary of template parameter values
        
    Returns:
        The formatted string with all {key} placeholders replaced
    """
    new_template = copy.deepcopy(template)
    for key, value in template_params.items():
        if hasattr(value, 'to_cpp'):
            value = value.to_cpp()
        elif isinstance(value, bool):
            value = 'true' if value else 'false'
        new_template = new_template.replace(f'{{{key}}}', str(value))
    return new_template


def jit(name: str, code: str, include_dirs: Optional[tuple[str]] = None, arch: Optional[str] = None, root: Optional[str] = None, flags: Optional[list[str]] = None) -> Runtime:
    """ Just-in-time compile a function.

    Args:
        name: The name of the function to compile.
        code: The code of the function to compile.
        include_dirs: The include directories to use for the compilation.
        arch: The architecture to use for the compilation.
        root: The root directory to store the compiled function.
        flags: The flags to use for the compilation.

    Returns:
        A Runtime callable that can be used to call the compiled function.
    """
    if flags is None:
        flags = compiler_flags(arch)
    if include_dirs is None:
        include_dirs = DEFAULT_INCLUDE_DIRS
    if root is None:
        root = DEFAULT_JIT_ROOT
    
    path = build_path(name=name, code=code, root=root, flags=flags)
    register_runtime(name, path)
    if Runtime.is_path_valid(path):
        logger.debug(f'Using cached runtime at {path}')
        runtime = Runtime(path)
    else:
        runtime = compile(code=code, include_dirs=include_dirs, arch=arch, path=path, flags=flags)

    return runtime

# This is currently unused, keeping it around for future reference
def parallel_jit(jobs: list[tuple[str, str, tuple[str], Optional[str], str, Optional[list[str]]]], max_workers: int = 8, allow_failure: bool = True, verbose: bool = False) -> list[Runtime]:
    """ Just-in-time compile a list of functions in parallel.

    Args:
        jobs: A list of tuples, each containing the arguments for the jit function.
        max_workers: The maximum number of workers to use.
        allow_failure: Whether to allow failure of some jobs. If False, all jobs must succeed. If True, failed jobs will have None in the output list.
        verbose: Whether to print verbose output.

    Returns:
        A list of Runtime objects that can be used to call the compiled functions.
    """
    workers =  min(len(jobs), max_workers)
    runtimes = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(jit, *job) for job in jobs]
        with tqdm(total=len(futures), desc="JITing", disable=not verbose) as pbar:
            for future in concurrent.futures.as_completed(futures):
                pbar.update(1)
                try:
                    runtimes.append(future.result())
                except Exception as e:
                    if not allow_failure:
                        raise e
                    if verbose:
                        logger.warning(f"Error during JIT: {e}")
                    else:
                        logger.debug(f"Error during JIT: {e}")
                    runtimes.append(None)
    return runtimes
