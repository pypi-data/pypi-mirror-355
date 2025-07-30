from RPG import Dado
from typing import Literal

from ...od2.data import DATA
from ...od2.helpers import jogada_ataque


TIPOS_EQUIPAMENTOS = Literal[
    'armadura',
    'recipiente',
    'veículo',
    'item',
    'escudo',
    'arma'
]


def buscar_equipamento(busca: str, chave: str = 'id'):
    """Busca um equipamento na api
    Args:
        busca (str): o id do equipamento a ser buscado. Pode ser também o nome
        chave (str, optional): se a busca é por id ou nome. Defaults to 'id'.

    Returns:
        dict: o dicionário com os dados do equipamento
    """

    resultado = [item for item in DATA.EQUIPAMENTOS if item[chave] == busca]
    return resultado[0]


def filtrar_equipamento(tipo: str):
    dicionario = {
        'armadura': 'armor', 
        'recipiente': 'container', 
        'veículo': 'vehicle', 
        'item': 'misc', 
        'escudo': 'shield', 
        'arma': 'weapon'
    }
    return [item for item in DATA.EQUIPAMENTOS if item['concept'] == dicionario[tipo]]


class Equipamento:
    def __init__(self, data: dict):
        self.data = data

    def __str__(self):
        return f'{self.__class__.__name__}(data["id"]="{self.data['id']}")'

    def __repr__(self):
        return f'{self.__class__.__name__}(data["id"]="{self.data['id']}")'


    #! Propriedades
    @property
    def peso(self):
        gramas = self.data['weight_in_grams']
        load = self.data['weight_in_load']

        gramas = gramas / 1000 if gramas else 0
        load = load if load else 0

        return gramas + load
        
    @property
    def preco(self):
        return self.data['cost']


class Arma(Equipamento):
    def __init__(self, data: str, ataque: int = 0):
        super().__init__(data)
        self.ataque = ataque

    #! Propriedades
    @property
    def propriedades(self):
        lista = self.data['description'].split(', ')
        lista[-1] = lista[-1].replace('.', '') # retira o ponto final do último item
        return lista
    
    @property
    def dano(self):
        return self.data['damage']
    
    #! Métodos
    def rolar_dano(self):
        if self.dano:
            converte_dado = [int(i) for i in self.dano.split('d')]
            return Dado(*converte_dado)


class Armadura(Equipamento):
    def __init__(self, data: str, equipada: bool = False):
        super().__init__(data)
        self.equipada = equipada

    #! Propriedades
    @property
    def ca(self):
        return self.data['bonus_ca']
    

class Escudo(Armadura):
    def __init__(self, data: str, equipado: bool = False):
        super().__init__(data, equipado)
