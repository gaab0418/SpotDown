"""
Spotify Downloader API - Educational Project
Copyright (c) 2025 https://github.com/gaab0418

This project is for educational purposes only.
Licensed under MIT License - see LICENSE file for details.


Arquivo principal para o Spotify Downloader API
"""
import os
import re
import uuid
import uvicorn
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

# Importar módulos do aplicativo
from config import API_HOST, API_PORT, JWT_ACCESS_TOKEN_EXPIRE_MINUTES
from database import get_db, init_db
from models import (
    User, SpotifyConfig, Download, 
    UserCreate, UserResponse, UserUpdate, Token,
    SpotifyConfigCreate, SpotifyConfigResponse,
    SpotifyUrl, SpotifyId,
    DownloadRequest, DownloadStatus, DownloadResponse,
    SearchResult
)
from auth import (
    get_password_hash, authenticate_user, create_access_token,
    get_current_active_user, get_admin_user
)
from download_queue import init_download_manager, get_download_manager

# Inicializar aplicação FastAPI
app = FastAPI(
    title="Spotify Downloader API",
    description="API para download de música e playlists do Spotify",
    version="2.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todas as origens
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos os métodos
    allow_headers=["*"],  # Permitir todos os headers
)

# --- Eventos de inicialização e encerramento ---

@app.on_event("startup")
async def startup_event():
    """Evento executado na inicialização da aplicação"""
    # Inicializar banco de dados
    init_db()
    
    # Inicializar gerenciador de downloads
    db = next(get_db())
    init_download_manager(db)
    
    print("API inicializada com sucesso!")

@app.on_event("shutdown")
async def shutdown_event():
    """Evento executado no encerramento da aplicação"""
    # Encerrar gerenciador de downloads
    try:
        download_manager = get_download_manager()
        download_manager.shutdown()
    except Exception as e:
        print(f"Erro ao encerrar gerenciador de downloads: {str(e)}")
    
    print("API encerrada com sucesso!")

# --- Rotas da API ---

@app.get("/")
async def root():
    """Rota raiz para verificar se a API está funcionando"""
    return {
        "message": "Spotify Downloader API está funcionando", 
        "version": "2.0.0",
        "docs": "/docs"
    }

# --- Rotas de Autenticação ---

@app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Criar um novo usuário"""
    # Verificar se o nome de usuário já existe
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Nome de usuário já cadastrado")
    
    # Verificar se o e-mail já existe
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")
    
    # Criar novo usuário
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        is_admin=False
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Endpoint para obter token de acesso"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nome de usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Obter dados do usuário atual"""
    return current_user

@app.put("/users/me", response_model=UserResponse)
async def update_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Atualizar dados do usuário atual"""
    user = db.query(User).filter(User.id == current_user.id).first()
    
    if user_update.email is not None:
        # Verificar se o e-mail já está em uso
        existing_user = db.query(User).filter(User.email == user_update.email).first()
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(status_code=400, detail="E-mail já está em uso")
        user.email = user_update.email
    
    if user_update.password is not None:
        user.hashed_password = get_password_hash(user_update.password)
    
    db.commit()
    db.refresh(user)
    
    return user

# --- Rotas para administração de usuários (apenas admin) ---

@app.get("/admin/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0, 
    limit: int = 100, 
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Listar todos os usuários (apenas admin)"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@app.put("/admin/users/{user_id}", response_model=UserResponse)
async def admin_update_user(
    user_id: int,
    user_update: UserUpdate,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Atualizar usuário (apenas admin)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    if user_update.email is not None:
        # Verificar se o e-mail já está em uso
        existing_user = db.query(User).filter(User.email == user_update.email).first()
        if existing_user and existing_user.id != user_id:
            raise HTTPException(status_code=400, detail="E-mail já está em uso")
        user.email = user_update.email
    
    if user_update.password is not None:
        user.hashed_password = get_password_hash(user_update.password)
    
    db.commit()
    db.refresh(user)
    
    return user

@app.delete("/admin/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Deletar usuário (apenas admin)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Não permitir que o admin se exclua
    if user.id == admin_user.id:
        raise HTTPException(status_code=400, detail="Não é possível excluir o próprio usuário admin")
    
    db.delete(user)
    db.commit()
    
    return None

# --- Rotas para configuração do Spotify ---

@app.get("/spotify/config", response_model=SpotifyConfigResponse)
async def get_spotify_config(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obter configuração do Spotify do usuário atual"""
    config = db.query(SpotifyConfig).filter(SpotifyConfig.user_id == current_user.id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    
    return config

@app.post("/spotify/config", response_model=SpotifyConfigResponse)
async def create_spotify_config(
    config: SpotifyConfigCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Criar ou atualizar configuração do Spotify para o usuário atual"""
    # Verificar se já existe configuração
    db_config = db.query(SpotifyConfig).filter(SpotifyConfig.user_id == current_user.id).first()
    
    if db_config:
        # Atualizar configuração existente
        for key, value in config.dict().items():
            setattr(db_config, key, value)
    else:
        # Criar nova configuração
        db_config = SpotifyConfig(user_id=current_user.id, **config.dict())
        db.add(db_config)
    
    # Garantir que o diretório de downloads existe
    user_download_path = os.path.join(config.download_path, f"user_{current_user.id}")
    if not os.path.exists(user_download_path):
        os.makedirs(user_download_path)
    
    db.commit()
    db.refresh(db_config)
    
    return db_config

# --- Rotas para extração de ID e pesquisa ---

@app.post("/extract-id", response_model=SpotifyId)
async def extract_id(spotify_url: SpotifyUrl):
    """Extrair ID a partir de uma URL do Spotify"""
    try:
        url = spotify_url.url
        
        # Padrões para URLs do Spotify
        patterns = [
            r"spotify.com/track/([a-zA-Z0-9]+)",
            r"spotify.com/playlist/([a-zA-Z0-9]+)",
            r"spotify.com/intl-[a-z]+/track/([a-zA-Z0-9]+)",
            r"spotify.com/intl-[a-z]+/playlist/([a-zA-Z0-9]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                spotify_id = match.group(1)
                
                # Determinar o tipo (track ou playlist)
                if "track" in url:
                    return {"id": spotify_id, "type": "track"}
                elif "playlist" in url:
                    return {"id": spotify_id, "type": "playlist"}
        
        raise HTTPException(status_code=400, detail="URL inválida. Use uma URL de faixa ou playlist do Spotify.")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Erro ao extrair ID: {str(e)}")

@app.get("/search", response_model=Dict[str, List[SearchResult]])
async def search_spotify(
    query: str = Query(..., description="Termo de busca"),
    type: str = Query("track", description="Tipo de busca (track ou playlist)"),
    limit: int = Query(5, description="Número máximo de resultados"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Pesquisar no Spotify"""
    try:
        # Verificar se usuário possui configuração do Spotify
        config = db.query(SpotifyConfig).filter(SpotifyConfig.user_id == current_user.id).first()
        if not config:
            raise HTTPException(
                status_code=400, 
                detail="Você não possui configuração do Spotify. Configure primeiro."
            )
        
        # Inicializar downloader
        from downloader import SpotifyDownloader
        downloader = SpotifyDownloader(db, current_user.id)
        
        # Executar pesquisa
        results = downloader.search(query, limit, type)
        return {"results": results}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Erro na pesquisa: {str(e)}")

# --- Rotas para downloads ---

@app.post("/downloads", response_model=DownloadStatus)
async def start_download(
    download_request: DownloadRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Iniciar download de faixa ou playlist"""
    try:
        # Verificar se usuário possui configuração do Spotify
        config = db.query(SpotifyConfig).filter(SpotifyConfig.user_id == current_user.id).first()
        if not config:
            raise HTTPException(
                status_code=400, 
                detail="Você não possui configuração do Spotify. Configure primeiro."
            )
        
        # Verificar se o tipo é válido
        if download_request.type not in ["track", "playlist"]:
            raise HTTPException(status_code=400, detail="Tipo inválido. Use 'track' ou 'playlist'")
        
        # Adicionar à fila de downloads
        download_manager = get_download_manager()
        download_id = download_manager.enqueue_download(
            current_user.id,
            download_request.spotify_id,
            download_request.type,
            download_request.priority
        )
        
        return {
            "status": "na_fila", 
            "message": f"Download de {download_request.type} adicionado à fila", 
            "download_id": download_id
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar download: {str(e)}")

@app.get("/downloads/{download_id}", response_model=DownloadResponse)
async def get_download_status(
    download_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obter status de um download específico"""
    download = db.query(Download).filter(
        Download.download_id == download_id, 
        Download.user_id == current_user.id
    ).first()
    
    if not download:
        raise HTTPException(status_code=404, detail="Download não encontrado")
    
    return download

@app.delete("/downloads/{download_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_download(
    download_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cancelar um download em andamento"""
    download = db.query(Download).filter(
        Download.download_id == download_id, 
        Download.user_id == current_user.id
    ).first()
    
    if not download:
        raise HTTPException(status_code=404, detail="Download não encontrado")
    
    # Cancelar download
    download_manager = get_download_manager()
    result = download_manager.cancel_download(download_id, current_user.id)
    
    if not result:
        raise HTTPException(status_code=500, detail="Não foi possível cancelar o download")
    
    return None

@app.get("/downloads", response_model=List[DownloadResponse])
async def list_downloads(
    status: Optional[str] = Query(None, description="Filtrar por status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Listar todos os downloads do usuário"""
    query = db.query(Download).filter(Download.user_id == current_user.id)
    
    if status:
        if status not in ["na_fila", "processando", "concluido", "erro", "cancelado"]:
            raise HTTPException(status_code=400, detail="Status inválido")
        query = query.filter(Download.status == status)
    
    return query.order_by(Download.created_at.desc()).all()

@app.get("/queue/status")
async def get_queue_status(
    current_user: User = Depends(get_current_active_user)
):
    """Obter status da fila de downloads"""
    download_manager = get_download_manager()
    queue_status = download_manager.get_queue_status()
    
    # Obter downloads ativos do usuário atual
    active_downloads = queue_status["active_downloads"]
    queue_size = queue_status["queue_size"]
    
    return {
        "active_downloads": active_downloads,
        "queue_size": queue_size,
        "max_concurrent": queue_status["max_concurrent"]
    }

# --- Rota para servir arquivos ---

@app.get("/files/{file_path:path}")
async def get_file(
    file_path: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Servir um arquivo de download"""
    # Verificar se o arquivo pertence ao usuário
    download = db.query(Download).filter(
        Download.file_path.endswith(file_path), 
        Download.user_id == current_user.id
    ).first()
    
    if not download:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    # Verificar se o arquivo existe
    if not os.path.exists(download.file_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no sistema")
    
    # Obter tipo de arquivo
    file_type = "audio/mpeg" if download.file_path.endswith(".mp3") else "application/octet-stream"
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=download.file_path,
        media_type=file_type,
        filename=os.path.basename(download.file_path)
    )

# --- Iniciar a aplicação ---

if __name__ == "__main__":
    uvicorn.run("main:app", host=API_HOST, port=API_PORT, reload=True)