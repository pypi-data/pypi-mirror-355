from ..data import DATA

def retorna_mod_atributo(valor: int):
    lista = DATA.ATRIBUTOS_MOD.keys()

    return next((DATA.ATRIBUTOS_MOD[x] for x in lista if x >= valor), None)
