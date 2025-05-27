"""
Spotify Downloader API - Educational Project
Copyright (c) 2025 https://github.com/gaab0418

This project is for educational purposes only.
Licensed under MIT License - see LICENSE file for details.

Arquivo de configuração para o Spotify Downloader
"""
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do MySQL
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "spotify_downloader")

# Configuração do JWT (JSON Web Token)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "chave_secreta_temporaria")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Configuração padrão do Spotify
DEFAULT_SPOTIFY_CONFIG = {
    "client_id": os.getenv("SPOTIFY_CLIENT_ID", ""),
    "client_secret": os.getenv("SPOTIFY_CLIENT_SECRET", ""),
    "redirect_uri": os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback"),
    "download_path": os.getenv("DOWNLOAD_PATH", "./downloads")
}

# Configuração da API
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8801"))

# Configuração da fila de downloads
MAX_CONCURRENT_DOWNLOADS = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "3"))