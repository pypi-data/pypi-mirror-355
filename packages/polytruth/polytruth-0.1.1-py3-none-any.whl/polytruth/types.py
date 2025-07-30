from typing import Protocol, TypeVar
import numpy as np
T = TypeVar('T')

class SupportsAddSub(Protocol):
    """支持加减运算的协议"""
    def __add__(self: T, other: T) -> T: ...
    def __sub__(self: T, other: T) -> T: ...

Computable =  float | int|np.ndarray
