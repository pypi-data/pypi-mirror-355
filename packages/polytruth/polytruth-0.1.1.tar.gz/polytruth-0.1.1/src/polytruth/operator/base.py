from abc import ABC, abstractmethod
from ..types import Computable
class Operators(ABC):
    """
    Abstract base class for logic operators.
    """
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def lor(self, a:Computable,b:Computable) -> Computable:
        """a \\\\/ a"""
        pass
    @abstractmethod
    def land(self,a:Computable,b:Computable)->Computable:
        """a /\\\\ b"""
        pass
    @abstractmethod
    def lnot(self,a:Computable)->Computable:
        """~ a"""
        pass
    @abstractmethod
    def implies(self,a:Computable,b:Computable)->Computable:
        """a-> b """
        pass
    @abstractmethod
    def equiv(self,a:Computable,b:Computable)-> Computable:
        """a<->b"""
        pass

    def __repr__(self):
        return f"Operator({self.name})"
