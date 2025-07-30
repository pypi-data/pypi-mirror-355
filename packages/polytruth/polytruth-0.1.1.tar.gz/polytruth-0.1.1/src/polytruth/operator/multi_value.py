from .base import Operators
from ..types import Computable

class MultiValuedOperators(Operators):
    """
    MultiValued logic operators
    """
    def __init__(self):
        super().__init__("MultiValued")
    def lor(self, a:Computable, b:Computable)->Computable:
        return a+b-a*b
    def land (self,a:Computable,b:Computable)->Computable:
        return a*b
    def lnot(self,a:Computable)->Computable:
        return 1-a
    def implies(self,a:Computable,b:Computable)->Computable:
        return self.lor(self.lnot(a),b) #1-a+b-a*b
    def equiv(self,a:Computable,b:Computable)->Computable:
        return self.land(self.implies(a,b),self.implies(b,a))
