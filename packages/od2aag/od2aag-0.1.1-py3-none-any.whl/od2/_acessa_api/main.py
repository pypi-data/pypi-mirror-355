import sys
import os
import json
from api import api_get

PASTA_SAIDA = "../od2/data/api"
os.makedirs(PASTA_SAIDA, exist_ok=True)

ENDPOINTS = {
    "campanhas": "campanhas",
    "classes": "classes",
    "equipamentos": "equipamentos",
    "livros": "livros",
    "magias": "magias",
    "monstros": "monstros",
    "personagens": "personagens",
    "racas": "racas",
}


def salvar_json(nome, conteudo):
    caminho = os.path.join(PASTA_SAIDA, f"{nome}.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(conteudo, f, indent=2, ensure_ascii=False)
    print(f"✔ Dados salvos em {caminho}")


def baixar(endpoint):
    print(f"⬇ Baixando dados de '{endpoint}'...")
    dados = api_get(ENDPOINTS[endpoint])
    salvar_json(endpoint, dados)


def main():
    if len(sys.argv) < 3 or sys.argv[1] != "baixar":
        print(
            "Uso: python main.py baixar [classes|equipamentos|livros|magias|monstros|racas]")
        return

    item = sys.argv[2].lower()
    if item not in ENDPOINTS:
        print(f"Erro: item desconhecido '{item}'.")
        return

    baixar(item)


if __name__ == "__main__":
    main()
