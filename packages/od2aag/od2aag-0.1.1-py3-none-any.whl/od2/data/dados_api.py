import json
import pathlib

from ..CONFIG import PREFIXO, URL_ESPECIFICAS


def converte_json(nome_arquivo: str):
    arquivo = pathlib.Path(f'src/od2/{PREFIXO}{URL_ESPECIFICAS[nome_arquivo]}').resolve()
    
    if arquivo.exists():
        with open(arquivo) as arquivo:
            return json.loads(arquivo.read())
    else:
        return f'arquivo *{PREFIXO}{URL_ESPECIFICAS[nome_arquivo]}* não encontrado'
    

def filtrar_acesso_completo(nome_arquivo: str):
    lista = converte_json(nome_arquivo)

    if 'access' not in lista[0].keys():
        return lista

    return list(filter(lambda x: x.get('access') == 'complete', lista))


classes = filtrar_acesso_completo('classes')
equipamentos = filtrar_acesso_completo('equipamentos')
livros = converte_json('livros')
magias = filtrar_acesso_completo('magias')
monstros = filtrar_acesso_completo('monstros')
racas = filtrar_acesso_completo('raças')
