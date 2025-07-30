import requests
import json

from ..od2.CONFIG import PREFIXO, URL_ESPECIFICAS, URL_BASE


def pegar_todos_dados(info_base: str):
    url = URL_BASE + URL_ESPECIFICAS[info_base]
    atual = 1
    tem_proximo = True
    dados_total = []

    while tem_proximo:
        resposta = requests.get(url, params={'page': atual})
        data = resposta.json()
        header = resposta.headers.get('Link')

        dados_total.extend(data)

        if header and 'rel="next"' in header:
            atual += 1
        else:
            tem_proximo = False

    dados_total = [dado for dado in dados_total if 'access' not in dado.keys() or dado['access'] != "limited"]

    return dados_total


def gerar_arquivo(arquivo_base: str):
    with open(f'{PREFIXO}{URL_ESPECIFICAS[arquivo_base]}', 'w+') as arquivo:
        info = pegar_todos_dados(arquivo_base)
        arquivo.write(json.dumps(info, indent=2))



if __name__ == '__main__':
    print('Gerando os arquivos, aguarde')
    print('-'.ljust(50, '-'))

    for chave in URL_ESPECIFICAS.keys():
        print(f'Gerando {PREFIXO}{URL_ESPECIFICAS[chave]}')
        gerar_arquivo(chave)
        print(f'        {URL_ESPECIFICAS[chave]} finalizado')

    print('-'.ljust(30, '-'))
    print('Arquivos gerados')