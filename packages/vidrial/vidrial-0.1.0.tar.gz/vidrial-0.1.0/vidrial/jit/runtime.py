import ctypes
import os
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

from vidrial.jit.ctypes import map_ctype


class Runtime:
    def __init__(self, path: str, entrypoint: str = 'launch') -> None:
        self.path = path
        self.entrypoint = entrypoint
        self.lib = None

        assert Runtime.is_path_valid(self.path)

    @staticmethod
    def is_path_valid(path: str) -> bool:
        # Exists and is a directory
        if not os.path.exists(path) or not os.path.isdir(path):
            return False

        # Contains all necessary files
        files = ['kernel.cu', 'kernel.so']
        return all(os.path.exists(os.path.join(path, file)) for file in files)

    def __call__(self, *args) -> int:
        # Load SO file
        if self.lib is None:
            self.lib = ctypes.CDLL(os.path.join(self.path, 'kernel.so'))

        return_code = ctypes.c_int(0)
        cargs = [map_ctype(arg) for arg in args]
        self.lib[self.entrypoint](*cargs, ctypes.byref(return_code))
        return return_code.value



