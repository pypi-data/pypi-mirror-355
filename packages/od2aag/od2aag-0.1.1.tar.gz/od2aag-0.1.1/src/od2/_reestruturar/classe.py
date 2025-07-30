from ...od2.data import DATA


def buscar_classe(busca: str, chave: str = 'id'):
    """Busca uma classe na api
    Args:
        busca (str): o id da classe a ser buscado. Pode ser também o nome
        chave (str, optional): se a busca é por id ou name. Defaults to 'id'.

    Returns:
        dict: o dicionário com os dados da classe
    """

    resultado = [raca for raca in DATA.CLASSES if raca[chave] == busca]
    return resultado[0]


class Classe:
    def __init__(self, data: str):
        self.data = data


    def __str__(self):
        return f'Classe(data["id"]="{self.data['id']}")'

    def __repr__(self):
        return f'Classe(data["id"]="{self.data['id']}")'


    #! Propriedades
    @property
    def vida(self):
        pv_base = self.data['hp']
        pv_nivel_alto = self.data['high_level_hp_bonus']

        resultado = [pv_base]
        for _ in range(9):
            resultado.append(f'1d{pv_base}')

        for _ in range(5):
            resultado.append(pv_nivel_alto)

        return resultado

    @property
    def xp(self):
        return self._retornar_por_nivel('xp')

    @property
    def ba(self):
        return self._retornar_por_nivel('ba')

    @property
    def jp(self):
        return self._retornar_por_nivel('jp')

    @property
    def vida_bonus(self):
        lista = [0 for _ in range(15)]

        if self.data['id'] == 'barbaro':
            for i in range(15):
                lista[i] += 2

        if self.data['id'] == 'anao-aventureiro':
            for i in range(2, 10):
                self.vida[i] = '1d12'

        if self.data['id'] == 'elfo-aventureiro':
            for i in range(15):
                lista[i] += 1

        return lista
    

    #! Métodos privados
    def _retornar_por_nivel(self, chave: str):
        db = self.data['levels']

        valores = [db[i][chave] for i in db if chave in db[i].keys()]
        valores.insert(0, 0)

        return valores

