import hashlib
import functools
import os
import re
import subprocess
import uuid
import torch
from torch.utils.cpp_extension import CUDA_HOME
from pathlib import Path
from typing import Tuple, Iterable, Optional, Any, Dict
import tempfile
from vidrial.jit.runtime import Runtime
import logging

logger = logging.getLogger(__name__)


def hash_to_hex(s: str) -> str:
    md5 = hashlib.md5()
    md5.update(s.encode('utf-8'))
    return md5.hexdigest()[0:12]


@functools.lru_cache(maxsize=None)
def get_nvcc_compiler() -> Tuple[str, str]:
    paths = []
    if os.getenv('NVCC_COMPILER'):
        paths.append(os.getenv('NVCC_COMPILER'))
    paths.append(f'{CUDA_HOME}/bin/nvcc')

    # Try to find the first available NVCC compiler
    least_version_required = '12.2'
    version_pattern = re.compile(r'release (\d+\.\d+)')
    for path in paths:
        if os.path.exists(path):
            match = version_pattern.search(os.popen(f'{path} --version').read())
            version = match.group(1) # type: ignore
            assert match, f'Cannot get the version of NVCC compiler {path}'
            assert version >= least_version_required, f'NVCC {path} version {version} is lower than {least_version_required}'
            return path, version
    raise RuntimeError('Cannot find any available NVCC compiler')

def get_cuda_arch() -> Optional[str]:
    """Detect CUDA architecture of the local GPU, return None if CUDA is not available"""
    try:
        if not torch.cuda.is_available():
            return None
        dprops = torch.cuda.get_device_properties(torch.device('cuda'))
        name, major, minor = dprops.name, dprops.major, dprops.minor
        arch = f'{major}{minor}'
        arch = '90a' if arch == '90' else arch
        return arch
    except Exception:
        logger.warning('Cannot detect CUDA architecture, assuming 86')
        return None

def vidrial_include_dirs() -> list[str]:
    mosaic_dir = Path(__file__).parent.parent / 'mosaic'/ 'mosaics'
    mosaic_lib = Path(__file__).parent.parent
    mosaic_include = mosaic_lib / 'kernels'
    return [str(p) for p in [mosaic_dir, mosaic_lib, mosaic_include]]


def cutlass_include_dirs() -> list[str]:
    cutlass_dir = Path(__file__).parent.parent.parent / 'cutlass'
    cutlass_include = cutlass_dir / 'include'
    return [str(cutlass_include)]


def get_kernel_hash(code: str) -> str:
    """ A proper hash of the kernel requires a proper build system that tracks dependencies.
    This is a lightweight hash function that assumes that the JITted code only relies on vidrial headers (and cutlass).
    """
    md5 = hashlib.md5()
    mosaic_dir, _, kernel_dir = vidrial_include_dirs()
    for include_dir in [mosaic_dir, kernel_dir]:
        for root, _, files in os.walk(include_dir):
            for filename in sorted(files):
                if filename.endswith('.cuh'):
                    with open(os.path.join(root, filename), 'rb') as f:
                        md5.update(f.read())

    md5.update(code.encode('utf-8'))
    return md5.hexdigest()[0:12]


DEFAULT_INCLUDE_DIRS: tuple[str] = tuple(vidrial_include_dirs() + cutlass_include_dirs()) # type: ignore

def put(path, data, is_binary=False):
    # Write and do POSIX atomic replace
    tmpdir = tempfile.mkdtemp()
    tmp_file_path = f'{tmpdir}/file.tmp.{str(uuid.uuid4())}.{hash_to_hex(path)}'
    with open(tmp_file_path, 'wb' if is_binary else 'w') as f:
        f.write(data)
    os.replace(tmp_file_path, path)


def _make_hashable(x: Any) -> Any:
    """Convert a value into a hashable form for caching."""
    if isinstance(x, torch.Tensor):
        # For tensors, we use shape, dtype, and device as the key
        return (tuple(x.shape), str(x.dtype), str(x.device))
    elif isinstance(x, dict):
        return tuple((k, _make_hashable(v)) for k, v in sorted(x.items()))
    elif isinstance(x, (list, tuple)):
        return tuple(_make_hashable(v) for v in x)
    elif isinstance(x, (int, float, str, bool, type(None))):
        return x
    elif hasattr(x, '__str__'):
        # Handle C++ type objects that can be stringified
        return str(x)
    else:
        raise TypeError(f"Cannot make {type(x)} hashable for caching")


def compiler_flags(arch: Optional[str] = None) -> list[str]:
    if arch is None:
        arch = get_cuda_arch() or '86'
    nvcc_flags = ['-std=c++20', '-w', '-shared', '-O3', '--expt-relaxed-constexpr', '--expt-extended-lambda', '-ftemplate-backtrace-limit=0',
                  f'-gencode=arch=compute_{arch},code=sm_{arch}',
                  '--ptxas-options=--register-usage-level=10' + (',--verbose' if 'PTXAS_VERBOSE' in os.environ else ''),
                  # Suppress some unnecessary warnings, such as unused variables for certain `constexpr` branch cases
                  '--diag-suppress=177,174,940']
    cxx_flags = ['-fPIC', '-O3', '-Wno-deprecated-declarations', '-Wno-abi']
    
    if os.getenv('GCC_PROFILE_LEVEL', '0') == '1':  # Basic profiling
        cxx_flags.extend(['-ftime-report', '-fmem-report'])

    flags = [*nvcc_flags, f'--compiler-options={",".join(cxx_flags)}']
    return flags


def compile(code: str, include_dirs: Optional[tuple] = None, arch: Optional[str] = None, path: Optional[str] = None, flags: Optional[list[str]] = None) -> Runtime:
    """ Compile a CUDA kernel and return a Runtime object.

    Args:
        code: Code of the kernel.
        include_dirs: Include directories.
        arch: CUDA architecture.
        path: Path where shared object will be stored. Default to a temporary directory.

    Returns:
        A Runtime object.
    """
    if include_dirs is None:
        include_dirs = tuple(DEFAULT_INCLUDE_DIRS)

    if flags is None:
        flags = compiler_flags(arch)

    if path is None:
        path = tempfile.mkdtemp()

    # Write the code
    os.makedirs(path, exist_ok=True)
    src_path = f'{path}/kernel.cu'

    put(src_path, code)

    # Compile into a temporary SO file
    so_path = f'{path}/kernel.so'
    tmp_so_path = f'{path}/nvcc.tmp.{str(uuid.uuid4())}.{hash_to_hex(so_path)}.so'

    # Compile
    command = [
        get_nvcc_compiler()[0], src_path,
        '-o', tmp_so_path,
        *flags,
        *[f'-I{d}' for d in include_dirs]
    ]
    logger.debug(f'Compiling runtime with command {command}')

    res = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if res.returncode != 0:
        msg = f'Failed to compile {src_path}, {res.stdout.decode("utf-8") if res.stdout else "No stdout"}'
        logger.error(msg)
        raise RuntimeError(msg)
    
    logger.debug(f'Compilation output: {res.stdout.decode("utf-8") if res.stdout else ""}')

    # Atomic replace SO file
    os.replace(tmp_so_path, so_path)
    return Runtime(path)
