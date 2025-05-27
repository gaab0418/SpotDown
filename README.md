# Spotify Downloader API

⚠️ **AVISO IMPORTANTE: Este projeto é destinado EXCLUSIVAMENTE para fins educacionais e de aprendizado sobre Python e desenvolvimento de APIs. NÃO deve ser usado para download de conteúdo protegido por direitos autorais.**

Uma API RESTful para estudo de download de músicas e playlists do Spotify, utilizando FastAPI e processamento paralelo para gerenciar downloads simultâneos.

## 🎓 Propósito Educacional

Este projeto foi desenvolvido com o objetivo de:
- Aprender e demonstrar conceitos de desenvolvimento de APIs com Python
- Explorar o uso de bibliotecas e ferramentas modernas do ecossistema Python
- Estudar padrões de arquitetura de software e boas práticas
- Experimentar com processamento paralelo e gerenciamento de filas
- Compreender sistemas de autenticação e autorização

**⚖️ Responsabilidade Legal:** O usuário é responsável por garantir que qualquer uso deste código esteja em conformidade com as leis locais e termos de serviço das plataformas utilizadas.

## 🛠️ Tecnologias e Ferramentas Utilizadas

### Backend & Framework
- **FastAPI** - Framework web moderno e rápido para Python
- **Uvicorn** - Servidor ASGI para aplicações Python
- **Pydantic** - Validação de dados e configurações
- **SQLAlchemy** - ORM para Python
- **PyMySQL** - Driver MySQL para Python

### Autenticação & Segurança
- **python-jose** - Implementação JWT para Python
- **passlib** - Biblioteca para hash de senhas
- **bcrypt** - Função de hash criptográfica

### Integração de APIs
- **Spotipy** - Biblioteca cliente para API do Spotify
- **requests** - Biblioteca HTTP para Python

### Processamento de Mídia
- **yt-dlp** - Ferramenta para download de vídeos/áudios
- **FFmpeg** - Processamento e conversão de áudio (requisito externo)

### Utilitários
- **python-dotenv** - Carregamento de variáveis de ambiente
- **python-multipart** - Suporte para dados multipart/form-data

### Banco de Dados
- **MySQL** - Sistema de gerenciamento de banco de dados

## Características

- 🎵 Sistema de estudo para download de faixas e playlists
- 👥 Sistema de usuários com autenticação JWT
- 🔄 Gerenciamento de fila de downloads com processamento paralelo
- 📊 Acompanhamento de progresso em tempo real
- 🧩 Extração automática de ID de URL do Spotify
- 🔍 Busca integrada no Spotify
- 🛡️ Sistema de permissões para usuários e administradores

## Requisitos

- Python 3.9+
- MySQL
- FFmpeg (para processamento de áudio)
- Credenciais de API do Spotify (client_id e client_secret)

## Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/spotify-downloader-api.git
   cd spotify-downloader-api
   ```

2. Crie um ambiente virtual e ative-o:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # ou
   venv\Scripts\activate  # Windows
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure o arquivo `.env` na raiz do projeto:
   ```
   # Configuração do MySQL
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=sua_senha
   MYSQL_DATABASE=spotify_downloader
   
   # Configuração JWT
   JWT_SECRET_KEY=chave_secreta_aleatoria
   
   # Configuração do Spotify
   SPOTIFY_CLIENT_ID=seu_client_id
   SPOTIFY_CLIENT_SECRET=seu_client_secret
   SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
   
   # Configuração da API
   API_HOST=0.0.0.0
   API_PORT=8801
   
   # Configuração de downloads
   DOWNLOAD_PATH=./downloads
   MAX_CONCURRENT_DOWNLOADS=3
   ```

5. Crie o banco de dados MySQL:
   ```sql
   CREATE DATABASE spotify_downloader CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

6. Execute a aplicação:
   ```bash
   python main.py
   ```

## Primeiros Passos

1. Acesse a documentação Swagger da API em: `http://localhost:8801/docs`

2. Crie um usuário:
   ```bash
   curl -X POST "http://localhost:8801/users/" \
     -H "Content-Type: application/json" \
     -d '{"username": "seunome", "email": "seu@email.com", "password": "suasenha"}'
   ```

3. Obtenha um token de acesso:
   ```bash
   curl -X POST "http://localhost:8801/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=seunome&password=suasenha"
   ```

4. Configure suas credenciais do Spotify:
   ```bash
   curl -X POST "http://localhost:8801/spotify/config" \
     -H "Authorization: Bearer seu_token" \
     -H "Content-Type: application/json" \
     -d '{
       "client_id": "seu_client_id_spotify",
       "client_secret": "seu_client_secret_spotify",
       "redirect_uri": "http://127.0.0.1:8888/callback",
       "download_path": "./downloads"
     }'
   ```

5. Inicie um download de teste:
   ```bash
   curl -X POST "http://localhost:8801/downloads" \
     -H "Authorization: Bearer seu_token" \
     -H "Content-Type: application/json" \
     -d '{
       "spotify_id": "id_da_musica_ou_playlist",
       "type": "track",
       "priority": 5
     }'
   ```

## Estrutura do Projeto

```
spotify-downloader-api/
├── auth.py                # Autenticação e controle de acesso
├── config.py              # Configurações da aplicação
├── database.py            # Conexão com o banco de dados
├── download_queue.py      # Gerenciamento da fila de downloads
├── downloader.py          # Funções de download do Spotify
├── main.py                # Aplicação FastAPI principal
├── models.py              # Modelos SQLAlchemy e esquemas Pydantic
├── requirements.txt       # Dependências do projeto
├── .env                   # Variáveis de ambiente (não versionado)
├── .env.example           # Exemplo de configuração
├── README.md              # Documentação do projeto
└── CONTRIBUTING.md        # Guia de contribuição
```

## Fluxo de Funcionamento

1. O usuário autentica-se e recebe um token JWT
2. O usuário configura suas credenciais do Spotify
3. O usuário solicita um download de faixa ou playlist
4. O download é adicionado à fila com uma prioridade
5. O gerenciador de downloads processa os downloads em paralelo
6. O usuário pode acompanhar o progresso do download
7. Ao finalizar, o arquivo fica disponível para download

## Endpoints Principais

### Autenticação
- `POST /users/` - Criar novo usuário
- `POST /token` - Obter token de acesso
- `GET /users/me` - Dados do usuário atual

### Spotify
- `POST /spotify/config` - Configurar credenciais do Spotify
- `GET /spotify/config` - Obter configuração atual
- `GET /search` - Pesquisar no Spotify
- `POST /extract-id` - Extrair ID do Spotify de uma URL

### Downloads
- `POST /downloads` - Iniciar novo download
- `GET /downloads` - Listar downloads do usuário
- `GET /downloads/{download_id}` - Status de um download específico
- `DELETE /downloads/{download_id}` - Cancelar um download
- `GET /queue/status` - Status da fila de downloads
- `GET /files/{file_path}` - Baixar arquivo

### Admin
- `GET /admin/users` - Listar todos os usuários
- `PUT /admin/users/{user_id}` - Atualizar usuário
- `DELETE /admin/users/{user_id}` - Excluir usuário

## 📚 Conceitos Aprendidos

Este projeto demonstra diversos conceitos importantes:

- **Arquitetura de APIs REST** com FastAPI
- **Autenticação JWT** e controle de acesso
- **ORM com SQLAlchemy** para interação com banco de dados
- **Processamento assíncrono** e gerenciamento de filas
- **Integração com APIs externas** (Spotify API)
- **Validação de dados** com Pydantic
- **Middleware e CORS** para aplicações web
- **Estruturação de projetos Python** profissionais
- **Documentação automática** com OpenAPI/Swagger

## ⚠️ Disclaimers Importantes

- Este projeto é apenas para fins educacionais e de aprendizado
- Não incentivamos ou apoiamos o uso para download de conteúdo protegido por direitos autorais
- Os usuários são responsáveis por cumprir todas as leis aplicáveis e termos de serviço
- Este projeto não tem afiliação oficial com o Spotify

## 🗒️ A fazer

- Criar um frontend

## Contribuições

Contribuições educacionais são bem-vindas! Por favor, leia o arquivo [CONTRIBUTING.md](CONTRIBUTING.md) para mais informações sobre como contribuir de forma educativa para este projeto.

## Licença

Este projeto está licenciado sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

---

**Lembre-se:** Este é um projeto educacional. Use-o para aprender sobre desenvolvimento Python, APIs e arquitetura de software. Sempre respeite os direitos autorais e termos de serviço das plataformas utilizadas.