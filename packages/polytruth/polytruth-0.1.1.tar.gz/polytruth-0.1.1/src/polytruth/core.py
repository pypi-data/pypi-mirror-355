from .operator import Operators
from abc import ABC, abstractmethod
from .types import *
from typing import Optional, Union,overload


class Expr(ABC):
    @abstractmethod
    def compute(self,operators: Operators)->Computable:
        pass

    def __call__(self,operators: Operators):
        return self.compute(operators)
    def __and__(self,other):
        return And(self,other)
    def __or__(self,other):
        return Or(self,other)
    def __invert__(self):
        return Not(self)
    def __repr__(self):
        return self.__str__()
class Var(Expr):
    def __init__(self,name:str,init_value:Computable=0):
        self.__vname__=name
        # self.__params__:list[str]=params
        self.__value__:Computable=init_value
    def compute(self, operators: Operators)->Computable:
        return self.__value__
    def __str__(self):
        return self.__vname__
    def __eq__(self,other):
        return self.__vname__==other.__vname__
    def __hash__(self):
        return hash(self.__vname__)
    def __repr__(self):
        return f"{self.__str__()}={self.__value__}"
    @property
    def value(self)->Computable:
        return self.__value__

    @value.setter
    def value(self, value:Computable):
        # TODO: check 0<=value<=1
        self.__value__ = value
    @property
    def name(self)->str:
        return self.__vname__


class Or(Expr):
    def __init__(self,a:Expr,b:Expr):
        self.__a__=a
        self.__b__=b
    def compute(self,operators: Operators):
        return operators.lor(self.__a__(operators),self.__b__(operators))

    def __repr__(self):
        return self.__str__()
    def __str__(self):
        return f"({self.__a__} \\/ {self.__b__})"

class And(Expr):
    def __init__(self,a:Expr,b:Expr):
        self.__a__=a
        self.__b__=b
    def compute(self,operators: Operators):
        return operators.land(self.__a__(operators),self.__b__(operators))

    def __repr__(self):
        return self.__str__()
    def __str__(self):
        return f"({self.__a__} /\\ {self.__b__})"

class Not(Expr):
    def __init__(self,a:Expr):
        self.__a__=a
    def compute(self,operators: Operators):
        return operators.lnot(self.__a__(operators))

    def __repr__(self):
        return self.__str__()
    def __str__(self):
        return f"~{self.__a__}"

class Implies(Expr):
    def __init__(self,a:Expr,b:Expr):
        self.__a__=a
        self.__b__=b
    def compute(self,operators: Operators):
        return operators.implies(self.__a__(operators),self.__b__(operators))

    def __repr__(self):
        return self.__str__()
    def __str__(self):
        return f"({self.__a__} -> {self.__b__})"

class Equiv(Expr):
    def __init__(self,a:Expr,b:Expr):
        self.__a__=a
        self.__b__=b
    def compute(self,operators: Operators):
        return operators.equiv(self.__a__(operators),self.__b__(operators))

    def __repr__(self):
        return self.__str__()
    def __str__(self):
        return f"({self.__a__} <-> {self.__b__})"
