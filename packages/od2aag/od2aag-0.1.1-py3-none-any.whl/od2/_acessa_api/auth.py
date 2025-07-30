from config import *

import json
import webbrowser
import requests
from urllib.parse import urlencode


def save_token(data):
    with open(TOKEN_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_token():
    try:
        with open(TOKEN_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def authorize():
    params = {
        "cliente_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
        "prompt": "consent"
    }

    auth_url = f"{AUTHORIZATION_URL}?{urlencode(params)}"
    
    print('Abrindo o navegador para autenticação')
    webbrowser.open(auth_url)

    print('Após o login, copie do código da URL de callback e cole abaixo.')
    auth_code = input("Code: ".strip())

    token_data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "cliente_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    response = requests.post(TOKEN_URL, data=token_data)

    if response.status_code == 200:
        token = response.json()
        save_token(token)
        print("Token salvo com sucesso em token.json")
        return token
    else:
        print("Erro ao obter token:", response.text)
        return None
    

if __name__ == '__main__':
    token = authorize()
