"""Data types for C++ type system representation.

This module provides Python classes that represent C++ types and can generate
their C++ string representations. Used for JIT compilation and type system
manipulation.
"""

from .types import (
    # Enums
    CudaDType,
    
    # Core types
    Int,
    Shape,
    Stride,
    Layout,
    
    # Traits
    Trait,
    UniversalCopy,
    CopyAtom,

    # Common trait instances
    UniversalCopyFloat,
    UniversalCopyUint8,

    # Layouts
    compact_major,
)
from .util import layout_from_tensor
from .algorithms import merge, get
from .tuples import flatten, Tuple
from .int import _1, _2, _3, _4, _5, _6, _7, _8, _16, _32, _64, _128, _256

__all__ = [
    'CudaDType',
    'Int',
    'Shape',
    'Stride',
    'Layout',
    'Tuple',
    'Trait',
    'UniversalCopy',
    'CopyAtom',
    'flatten',
    'merge',
    'get',
    'compact_major',
    'layout_from_tensor',
    'UniversalCopyFloat',
    'UniversalCopyUint8',
    '_1',
    '_2',
    '_3',
    '_4',
    '_5',
    '_6',
    '_7',
    '_8',
    '_16',
    '_32',
    '_64',
    '_128',
    '_256',
]
