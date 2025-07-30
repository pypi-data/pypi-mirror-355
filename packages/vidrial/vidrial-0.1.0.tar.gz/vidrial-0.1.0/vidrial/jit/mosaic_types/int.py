from typing import Union, Any

class BaseType:
    """Base class for all C++ type representations."""
    def to_cpp(self) -> str:
        """Generate C++ string representation of the type."""
        raise NotImplementedError


    def __repr__(self) -> str:
        return str(self)

class Int(BaseType):
    """Represents a compile-time integer value."""
    def __init__(self, value: int):
        self.value = value

    def to_cpp(self, _=None) -> str:
        return f"Int<{self.value}>"
    
    def size(self) -> int:
        return self.value
    
    def __mul__(self, other: Union[int, 'Int']) -> 'Int':
        if isinstance(other, Int):
            return Int(self.value * other.value)
        else:
            return Int(self.value * other)
        
    def __rmul__(self, other: Union[int, 'Int']) -> 'Int':
        return self * other
    
    def __int__(self) -> int:
        return self.value
    
    def __str__(self) -> str:
        return str(self.value)
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(value={self.value})"
    
    def __reduce__(self):
        """Make Int picklable by specifying how to reconstruct it."""
        return (type(self), (self.value,))
    
    def __eq__(self, other: Union[int, 'Int']) -> bool:
        if isinstance(other, Int):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other
        else:
            raise ValueError(f"Cannot compare Int with {type(other)}")
        
    def __le__(self, other: Union[int, 'Int']) -> bool:
        if isinstance(other, Int):
            return self.value <= other.value
        elif isinstance(other, int):
            return self.value <= other
        else:
            raise ValueError(f"Cannot compare Int with {type(other)}")
        
    def __lt__(self, other: Union[int, 'Int']) -> bool:
        if isinstance(other, Int):
            return self.value < other.value
        elif isinstance(other, int):
            return self.value < other
        else:
            raise ValueError(f"Cannot compare Int with {type(other)}")
        
    def __ge__(self, other: Union[int, 'Int']) -> bool:
        if isinstance(other, Int):
            return self.value >= other.value
        elif isinstance(other, int):
            return self.value >= other
        else:
            raise ValueError(f"Cannot compare Int with {type(other)}")
        
    def __gt__(self, other: Union[int, 'Int']) -> bool:
        if isinstance(other, Int):
            return self.value > other.value
        elif isinstance(other, int):
            return self.value > other
        else:
            raise ValueError(f"Cannot compare Int with {type(other)}")

    def __pow__(self, other: Union[int, 'Int']) -> Union['Int', int]:
        if isinstance(other, Int):
            return Int(self.value ** other.value)
        else:
            return int(self.value ** other)

    def __truediv__(self, other: Union[int, 'Int']) -> Union['Int', int]:
        if isinstance(other, Int):
            return Int(self.value // other.value)
        else:
            return int(self.value // other)
        
    def __floordiv__(self, other: Union[int, 'Int']) -> Union['Int', int]:
        if isinstance(other, Int):
            return Int(self.value // other.value)
        else:
            return int(self.value // other)
        
    def __mod__(self, other: Union[int, 'Int']) -> Union['Int', int]:
        if isinstance(other, Int):
            return Int(self.value % other.value)
        else:
            return int(self.value % other)
        
    def __hash__(self) -> int:
        return hash(self.value)
        
        
def intify(value: Union[int, Any]) -> Any:
    if isinstance(value, int):
        return Int(value)
    return value

_1 = Int(1)
_2 = Int(2)
_3 = Int(3)
_4 = Int(4)
_5 = Int(5)
_6 = Int(6)
_7 = Int(7)
_8 = Int(8)
_9 = Int(9)
_10 = Int(10)
_16 = Int(16)
_32 = Int(32)
_64 = Int(64)
_128 = Int(128)
_256 = Int(256)
_512 = Int(512)
_1024 = Int(1024)
_2048 = Int(2048)
_4096 = Int(4096)
_8192 = Int(8192)
_16384 = Int(16384)