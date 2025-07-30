from .api.campanhas import campanhas
from .api.classes import classes
from .api.equipamentos import equipamentos
from .api.livros import livros
from .api.magias import magias
from .api.monstros import monstros
from .api.personagens import personagens
from .api.racas import racas

def filtrar_acesso_completo(variavel: str):
    lista = variavel

    if 'access' not in lista[0].keys():
        return lista

    return list(filter(lambda x: x.get('access') == 'complete', lista))


classes = filtrar_acesso_completo(classes)
equipamentos = filtrar_acesso_completo(equipamentos)
livros = livros
magias = filtrar_acesso_completo(magias)
monstros = filtrar_acesso_completo(monstros)
racas = filtrar_acesso_completo(racas)
