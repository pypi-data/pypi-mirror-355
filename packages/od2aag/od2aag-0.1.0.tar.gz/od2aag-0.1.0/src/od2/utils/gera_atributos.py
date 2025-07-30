from typing import Literal
from collections import namedtuple
from RPG.dado import Dado

from ..data import DATA


LISTA_ATRIBUTOS = Literal['FOR', 'DES', 'CON', 'INT', 'SAB', 'CAR']

ESTILOS = Literal[
    'clássico',
    'aventureiro',
    'heroico',
    # 'duplo',
    # 'camponês',
    # 'distribuição',
    # 'racial'
]

Atributos = namedtuple('Atributos', ('FOR', 'DES', 'CON', 'INT', 'SAB', 'CAR'))

def rolar_atributos(estilo: ESTILOS = 'clássico'):
    """Gera os atributos conforme o estilo de rolagem

    Args:
        estilo (ESTILOS, optional): escolha entre os estilos de rolamento. Defaults to 'clássico'.

    Returns:
        GeradorAtributos: Uma classe de gerador para atribuir os atributos
    """
    return GeradorAtributos(estilo)


class GeradorAtributos:
    def __init__(self, estilo: ESTILOS):
        self._estilo = estilo

        self._iniciar_escolhidos()
        self.rolar()
        self.rolamento_original = tuple(self.rolamento)

    def __repr__(self) -> str:
        return f'{self.atributos}'
    

    #? Métodos privados
    def _iniciar_escolhidos(self):
        self._ordem_escolhidos = [None for _ in range(6)]

    def _checar_rolamento_classico_aventureiro(self):
        if self._estilo == 'clássico' or self._estilo == 'aventureiro':
            self.rolamento = list(Dado(3, 6) for _ in range(6))
            self._rolamento_totais = list(rolamento.total for rolamento in self.rolamento)

    def _checar_rolamento_heroico(self):
        if self._estilo == 'heroico':
            self.rolamento = [Dado(4, 6) for _ in range(6)]

            retira_menor = list(self.rolamento)
            for dado in retira_menor:
                dado.retirar_menor()

            self._rolamento_totais = [rolamento.total for rolamento in retira_menor]

    def _aplicar_resultado_na_ordem(self):
        if self._estilo == 'clássico' or self._estilo == 'duplo':
            self._ordem_escolhidos = list(atr for atr in DATA.ATRIBUTOS)

    def _retornar_resultado_final(self):
        if None not in self._ordem_escolhidos:
            self._aplicar_lista_final()

        else:
            self._retorna_lista_incompleta()

    def _aplicar_lista_final(self):
        final = []
        for i in DATA.ATRIBUTOS:
            indice = self._ordem_escolhidos.index(i)
            final.append(self._rolamento_totais[indice])

        self.atributos = Atributos(*final)

    def _retorna_lista_incompleta(self):
        atributos_disponiveis = list(i for i in DATA.ATRIBUTOS if i not in self._ordem_escolhidos)
        valores_disponiveis = list(str(self._rolamento_totais[i]) for i, x in enumerate(
            self._ordem_escolhidos) if not x)

        self.atributos = f'Atributos não escolhidos: {", ".join(
            atributos_disponiveis)}. Valores disponíveis: {", ".join(valores_disponiveis)}'

    def _encontrar_indice_livre(self, valor_escolhido):
        for i, (valor, atributo) in enumerate(zip(self._rolamento_totais, self._ordem_escolhidos)):
            if valor == valor_escolhido and atributo is None:
                return i
            
        return None

    #? Métodos públicos
    def rolar(self):
        self._iniciar_escolhidos()
        self._checar_rolamento_classico_aventureiro()
        self._checar_rolamento_heroico()

        self._aplicar_resultado_na_ordem()
        self._retornar_resultado_final()

    def atribuir_atributo(self, atributo: LISTA_ATRIBUTOS, valor: int):
        indice = self._encontrar_indice_livre(valor)

        if indice is not None:
            self._ordem_escolhidos[indice] = atributo
        else:
            print(f'Não há {valor} livre. Use .zerar_atributo() ou .trocar_atributo() para zerar o reatribuir')

        self._retornar_resultado_final()

    def zerar_atributo(self, atributo: LISTA_ATRIBUTOS):
        if atributo in self._ordem_escolhidos:
            indice = self._ordem_escolhidos.index(atributo)
            self._ordem_escolhidos[indice] = None
        
        self._retornar_resultado_final()

    def trocar_atributos(self, atributo1: LISTA_ATRIBUTOS, atributo2: LISTA_ATRIBUTOS):
        if atributo1 in self._ordem_escolhidos and atributo2 in self._ordem_escolhidos:
            indice1 = self._ordem_escolhidos.index(atributo1)
            indice2 = self._ordem_escolhidos.index(atributo2)

            self._ordem_escolhidos[indice2] = atributo1
            self._ordem_escolhidos[indice1] = atributo2

        self._retornar_resultado_final()
