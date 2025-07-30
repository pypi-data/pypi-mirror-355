from dataclasses import dataclass

from .rolagens import teste_atributo
from .retorna_atributo import retorna_mod_atributo


@dataclass
class AtributoBase:
    valor: int


    #! Métodos
    def rolar(self, modificador: int = 0):
        return teste_atributo(self.valor, modificador)


@dataclass
class Atributo(AtributoBase):
    valor: int
    
    def __post_init__(self):
        self.modificadores = retorna_mod_atributo(self.valor)


    #! Propriedades
    @property
    def modificador(self):
        return self.modificadores.mod
    
    @property
    def circulo_1(self):
        return self.modificadores.circulo_1
    
    @property
    def circulo_2(self):
        return self.modificadores.circulo_2
    
    @property
    def circulo_3(self):
        return self.modificadores.circulo_3
    