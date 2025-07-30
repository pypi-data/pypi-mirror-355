import torch
from enum import Enum
from typing import Any, List, TypeVar, Union, Generic, Optional, Tuple
from vidrial.jit.mosaic_types.shape import Shape
from vidrial.jit.mosaic_types.stride import Stride
from vidrial.jit.mosaic_types.int import BaseType, Int, _1, _8, _32, _64, _128, _256

T = TypeVar('T')


class CudaDType(Enum):
    """Enum representing CUDA data types."""
    UINT8 = "uint8_t"
    FLOAT = "float"
    FLOAT32 = "float"
    DOUBLE = "double"
    FLOAT64 = "double"
    INT32 = "int32_t"
    INT64 = "int64_t"
    FLOAT16 = "half_t"
    BFLOAT16 = "bfloat16_t"

    def to_cpp(self) -> str:
        return self.value


def last(x: Union[Stride, Shape]) -> Int:
    """Get the last element of a Stride or Shape."""
    if isinstance(x.elements[-1], Int):
        return x.elements[-1]
    else:
        return last(x.elements[-1])


def compact_major(shape: Shape, left: bool = True, current: Int = _1) -> Stride:
    """Create a compact major Stride from a Shape."""
    elements = shape.elements if left else shape.elements[::-1]
    strides = []
    for elem in elements:
        if isinstance(elem, Int):
            strides.append(current)
            current *= elem
        elif isinstance(elem, Shape):
            stride = compact_major(elem, left, current)
            strides.append(stride)
            current = current * elem.size()
    return Stride(*strides) if left else Stride(*reversed(strides))


class Layout(BaseType):
    """Represents a layout type combining shape and stride."""
    def __init__(self, shape: Shape, stride: Optional[Stride] = None):
        self.shape = shape
        if stride is None:
            stride = compact_major(shape)
        self.stride = stride

    def to_tuple(self) -> Tuple[Tuple[Any, ...], Tuple[Any, ...]]:
        return (self.shape.to_tuple(), self.stride.to_tuple())
            
    def to_cpp(self) -> str:
        return f"Layout<{self.shape.to_cpp()}, {self.stride.to_cpp()}>"

    def __str__(self) -> str:
        return f"{self.shape}:{self.stride}"
    
    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Layout):
            return self.shape == other.shape and self.stride == other.stride
        return False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(shape={self.shape}, stride={self.stride})"
    
    def __reduce__(self):
        """Make Layout picklable by specifying how to reconstruct it."""
        return (type(self), (self.shape, self.stride))


class Trait(BaseType):
    """Base class for traits with name and dtype."""
    def __init__(self, name: str, dtype: CudaDType):
        self.name = name
        self.dtype = dtype

    def to_cpp(self) -> str:
        return f"{self.name}<{self.dtype.value}>"


class UniversalCopy(Trait):
    """Universal copy trait."""
    def __init__(self, dtype: CudaDType):
        super().__init__("UniversalCopy", dtype)


class CopyAtom(BaseType):
    """Represents a copy atom with trait and dtype."""
    def __init__(self, trait: Trait):
        self.trait = trait

    def to_cpp(self) -> str:
        return f"Copy_Atom<{self.trait.to_cpp()}, {self.trait.dtype.value}>"


ATOMS_A_F16_B_F16 = [
    "SM80_16x8x8_F32F16F16F32_TN",
    "SM80_16x8x16_F32F16F16F32_TN",
]

ATOMS_A_BF16_B_BF16 = [
    "SM80_16x8x8_F32BF16BF16F32_TN",
    "SM80_16x8x16_F32BF16BF16F32_TN"
]

ATOMS_A_TF32_B_TF32 = [
    "SM80_16x8x4_F32TF32TF32F32_TN",
    "SM80_16x8x8_F32TF32TF32F32_TN",
]

def get_valid_atoms(A: torch.Tensor, B: torch.Tensor) -> List[str]:
    """Get the valid atoms for a given pair of tensors."""
    if A.dtype == torch.float16 and B.dtype == torch.float16:
        return ATOMS_A_F16_B_F16
    elif A.dtype == torch.bfloat16 and B.dtype == torch.bfloat16:
        return ATOMS_A_BF16_B_BF16
    elif A.dtype == torch.float32 and B.dtype == torch.float32:
        return ATOMS_A_TF32_B_TF32
    else:
        raise ValueError(f"No valid atoms found for {A.dtype} and {B.dtype}")


# Common trait instances
UniversalCopyFloat = UniversalCopy(CudaDType.FLOAT)
UniversalCopyUint8 = UniversalCopy(CudaDType.UINT8)

