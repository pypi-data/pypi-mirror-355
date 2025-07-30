from config import *

import json
import time
import requests

def load_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            return json.load(f)
    return None

def save_token(token):
    token["obtido_em"] = int(time.time())
    with open(TOKEN_FILE, "w") as f:
        json.dump(token, f, indent=2)

def is_token_expired(token):
    if "expires_in" not in token or "obtido_em" not in token:
        return True
    expira_em = token["obtido_em"] + token["expires_in"] - 60  # margem de 60s
    return time.time() >= expira_em

def refresh_token():
    token = load_token()
    if not token or 'refresh_token' not in token:
        raise RuntimeError("Token ausente ou sem refresh_token")
    
    data = {
        "grant_type": "refresh_token",
        "refresh_token": token["refresh_token"],
        "cliente_id": CLIENT_ID,
        "cliente_secret": CLIENT_SECRET,
    }

    response = requests.post(TOKEN_URL, data=data)

    if response.status_code == 200:
        new_token = response.json()
        save_token(new_token)
        return new_token
    else:
        raise RuntimeError(f"Erro ao renovar token {response.text}")
    
def get_valid_token():
    token = load_token()

    if not token:
        raise RuntimeError('Token não encontrado. Execute auth.py primeiro')
    
    if is_token_expired(token):
        print('Token expirado ou ausente. Renovando...')
        token = refresh_token()

    return token['access_token']

def api_get(endpoint):
    retorna_header: lambda token_acesso: {
        "Authorization": f"Bearer {token_acesso}",
        "User-Agent": USER_AGENT,
        "Accept": "application/json"
    }

    access_token = get_valid_token()

    headers = retorna_header(access_token)

    url = f"https://olddragon.com.br/api/{endpoint}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 401:
        print("Token rejeitado. Renovando...")
        access_token = refresh_token()["access_token"]
        headers = retorna_header(access_token)
        response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        raise RuntimeError(f"Erro na chamada: {response.status_code} {response.text}")

