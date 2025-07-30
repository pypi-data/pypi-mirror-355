import os

# identificação
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

# autenticação
AUTHORIZATION_URL = "https://olddragon.com.br/authorize"
TOKEN_URL = "https://olddragon.com.br/token"
REDIRECT_URI = "https://postman-echo.com/post"

# escopo autorizado
SCOPE = "openid email content.read offline_access"

# api base
API_BASE_URL = "https://olddragon.com.br/"

# cabeçalho de identifcação
USER_AGENT = "OD2 (alessandro.guarita@gmail.com)"

# caminho local para armazenar o token
TOKEN_FILE = "token.json"
