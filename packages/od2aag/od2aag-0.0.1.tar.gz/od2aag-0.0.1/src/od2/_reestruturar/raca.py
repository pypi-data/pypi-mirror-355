from ..od2.data import DATA

def buscar_raca(busca: str, chave: str = 'id'):
    """Busca uma raça na api
    Args:
        busca (str): o id da raça a ser buscado. Pode ser também o nome
        chave (str, optional): se a busca é por id ou nome. Defaults to 'id'.

    Returns:
        dict: o dicionário com os dados da raça
    """

    resultado = [raca for raca in DATA.RACAS if raca[chave] == busca]
    return resultado[0]


class Raca:
    def __init__(self, data: str):
        self.data = data

    def __str__(self):
        return f'Raca(data["id"]="{self.data['id']}")'

    def __repr__(self):
        return f'Raca(data["id"]="{self.data['id']}")'


    #! Propriedades
    @property
    def movimento(self):
        return self.data['movement']

    @property
    def infravisao(self):
        return self.data['infravision']

    @property
    def alinhamento(self):
        return self.data['alignment_tendency']