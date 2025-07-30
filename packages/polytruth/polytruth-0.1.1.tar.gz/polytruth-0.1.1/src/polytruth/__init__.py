
from typing import Optional, Union,overload
from types import MappingProxyType

from .core import *
from .operator import *
from .types import *
class LogicSystem:
    """A logic system that can be used to reason."""
    def __init__(self,ops:Operators):
        """
        Initialize the logic system with the given operators.
        Args:
            ops (Operators): The operators to be used in the logic system.
        """
        self.__variables__: dict[str,Var] = dict()
        self.__rules__:dict[str,Expr] = dict()
        self.__ops__ = ops
    def add_rule(self, name, rule):
        """

        """
        self.__rules__[name] = rule
    def add_variable(self,variable:Var)->Var:
        """
        Add a variable
        Args:
            variable (Var): variable
        Returns:
            Var
        """
        if variable.name in self.__variables__:
            # print(f"Variable {variable.name} already exists")
            return self.__variables__[variable.name]
        self.__variables__[variable.name] = variable
        return variable
    def new_variable(self, name:str,init_value:Computable=0.0)->Var:
        """
        Create new variable withe name
        """
        var=Var(name,init_value)
        return self.add_variable(var)
    def set_variable_value(self, name:str, value:Computable):
        """
        Set a variable value with name
        """
        self.__variables__[name].value=value
    def set_variable_values(self, values:dict[str,Computable]):
        for name, value in values.items():
            if name in self.__variables__:
                self.__variables__[name].value=value
    @property
    def rules(self):
        return MappingProxyType(self.__rules__)
    @property
    def variables(self):
        return MappingProxyType(self.__variables__)
    @overload
    def compute(
                self,
                name: str,
                valuses: Optional[dict[str, Computable]] = None
            ) -> Computable: ...

    @overload
    def compute(
                self,
                name: None = None,
                valuses: Optional[dict[str, Computable]] = None
            ) -> list[tuple[str, Computable]]: ...

    def compute(self,name:Optional[str]=None,valuses:Optional[dict[str,Computable]]=None)->Union[Computable,list[tuple[str,Computable]]]:
        if valuses is not None:
            self.set_variable_values(valuses)
        if name is None:
            return [(name, rule(self.__ops__)) for name,rule in self.__rules__.items()]
        return self.__rules__[name](self.__ops__)
    @overload
    def __call__(
                    self,
                    name: str,
                    valuse: Optional[dict[str, Computable]] = None
                ) -> Computable: ...

    @overload
    def __call__(
                    self,
                    name: None = None,
                    valuse: Optional[dict[str, Computable]] = None
                ) -> list[tuple[str, Computable]]: ...
    def __call__(self,name:Optional[str]=None,valuse:Optional[dict[str,Computable]]=None)->Union[Computable,list[tuple[str,Computable]]]:
        return self.compute(name,valuse)
