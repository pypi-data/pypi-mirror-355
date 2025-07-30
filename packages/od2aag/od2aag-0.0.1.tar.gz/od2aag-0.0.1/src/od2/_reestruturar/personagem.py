from typing import Literal
from RPG import rolar_dado_notacao

from ..od2.utils.gera_atributos import Atributos
from ..od2.helpers import Atributo, AtributoBase, Moedas
from .raca import buscar_raca, Raca
from .classe import buscar_classe, Classe


ALINHAMENTOS = Literal[
    'ordeiro',
    'neutro',
    'caótico'
]


class Personagem:
    def __init__(self,
                 nome: str,
                 atributos: tuple | Atributos,
                 raca: dict | str,
                 classe: dict | str,
                 alinhamento: ALINHAMENTOS,
                 xp: int = 0,
                 vida: list | None = None,
                 vida_atual: int | None = None,
                 modificadores: dict | None = None,
                 moedas: dict | None = None,
                 ):
        
        self._atributos = atributos if type(atributos) is Atributos else Atributos(*atributos)
        self._raca = raca
        self._classe = classe
        self._xp = xp
        self._vida = vida
        self._vida_atual = vida_atual

        self.nome = nome
        self.alinhamento = alinhamento.capitalize()
        self.moedas = Moedas(moedas) if moedas else Moedas(0, 0, 0)
        self.modificadores = modificadores if modificadores else dict()

        self._ajustar_raca()
        self._ajustar_classe()
        self._ajustar_lista_vida()


    def __repr__(self) -> str:
        return f"Personagem(classe='{self.classe.data['name']}', raça='{self.raca.data['name']}', alinhamento='{self.alinhamento}', nivel={self.nivel})"

    def __str__(self):
        return f'{self.nome}: {self.classe.data['name']} {self.raca.data['name']} {self.alinhamento}, nível {self.nivel}'


    #! Propriedades
    @property
    def _modificadores_vida(self):
        lista = self.classe.vida_bonus

        for i in range(10):
            lista[i] += self.CON.modificador

        return lista

    @property
    def FOR(self):
        return Atributo(self._atributos.FOR)

    @property
    def DES(self):
        return Atributo(self._atributos.DES)

    @property
    def CON(self):
        return Atributo(self._atributos.CON)

    @property
    def INT(self):
        return Atributo(self._atributos.INT)

    @property
    def SAB(self):
        return Atributo(self._atributos.SAB)

    @property
    def CAR(self):
        return Atributo(self._atributos.CAR)
    

    @property
    def raca(self):
        return self._raca
    
    @property
    def classe(self):
        return self._classe
    
    @property
    def xp(self):
        return self._xp
    
    @property
    def nivel(self):
        xps = self.classe.xp

        xp_proximo_nivel = next((i for i in xps if i > self.xp), None)
        nivel = xps.index(xp_proximo_nivel) if xp_proximo_nivel else 15

        return nivel
    

    @property
    def JP(self):
        mod = self._retornar_modificador('jp')
        return self.classe.jp[self.nivel] + mod

    @property
    def JPC(self):
        mod = self._retornar_modificador('jpc')
        return AtributoBase(self.JP + self.CON.modificador + mod)

    @property
    def JPD(self):
        mod = self._retornar_modificador('jpd')
        return AtributoBase(self.JP + self.DES.modificador + mod)

    @property
    def JPS(self):
        mod = self._retornar_modificador('jps')
        return AtributoBase(self.JP + self.SAB.modificador + mod)
    

    @property
    def BA(self):
        return self.classe.ba[self.nivel]

    @property
    def BAD(self):
        return self.BA + self.DES.modificador

    @property
    def BAC(self):
        return self.BA + self.FOR.modificador


    @property
    def vida(self):
        mod_vida = self._modificadores_vida[:self.nivel]
        lista_resultante = [max(a + b, 1) for a, b in zip(mod_vida, self._vida)]

        return sum(lista_resultante)
    
    @property
    def vida_atual(self):
        self._vida_atual = self._vida_atual if type(
            self._vida_atual) is int else self.vida
        self._vida_atual = min(max(self._vida_atual, 0), self.vida)

        return self._vida_atual

    @vida_atual.setter
    def vida_atual(self, valor: int):
        self._vida_atual = valor

    
    @property
    def movimento(self):
        return self.raca.movimento
    
    @property
    def habilidades(self):
        habilidades = []

        if self.raca.infravisao:
            habilidades += [{
                'name': 'Infravisão',
                'description': f'infravisão de {self.raca.infravisao} metros'
            }]

        de_raca = self.raca.data['abilities']

        de_classe = [habilidade for habilidade in self.classe.data['abilities']
                     if habilidade['level'] <= self.nivel]

        return habilidades + de_raca + de_classe

    @property
    def carga_maxima(self):
        modificador = self._retornar_modificador('carga')

        return max(self.FOR.valor, self.CON.valor) + modificador


    #! Métodos inicializadores ou privados
    def _ajustar_raca(self):
        if type(self._raca) is str:
            self._raca = buscar_raca(self._raca)

        self._raca = Raca(self._raca)

    def _ajustar_classe(self):
        if type(self._classe) is str:
            self._classe = buscar_classe(self._classe)

        self._classe = Classe(self._classe)

    def _ajustar_lista_vida(self):
        # cria a lista base para o caso de já não ter valores rolados
        if not self._vida:
            self._vida = [self.classe.vida[0]]

        # retira o excesso de dados, caso tenha mais que o nível
        if len(self._vida) > self.nivel:
            self._vida = self._vida[0:self.nivel]

    def _retornar_modificador(self, chave: str):
        modificador = 0
        if chave in self.modificadores.keys():
            modificador += sum(self.modificadores[chave].values())

        return modificador

    #! Métodos
    def aplicar_xp(self, valor_recebido: int):
        modificador = 1

        if self._raca == 'humano':
            modificador += .1

        if self._raca == 'meio-elfo':
            modificador += .05

        valor_recebido = int(valor_recebido * modificador)
        self._xp += valor_recebido

    def rolar_vida(self):
        """
        Rola a vida de todos os níveis não rolados
        """
        while len(self._vida) < self.nivel:
            vida_atual = self.classe.vida[len(self._vida)]
            vida_atual = rolar_dado_notacao(vida_atual) if type(
                vida_atual) is str else vida_atual

            self._vida.append(vida_atual)

    def drenar_nivel(self, qtd_drenado: int):
        # TODO
        pass