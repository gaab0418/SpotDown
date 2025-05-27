"""
Spotify Downloader API - Educational Project
Copyright (c) 2025 https://github.com/gaab0418

This project is for educational purposes only.
Licensed under MIT License - see LICENSE file for details.


Modelos do banco de dados e esquemas Pydantic
"""
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any, Annotated
from datetime import datetime as py_datetime

# Define SQLAlchemy DateTime as annotated datetime for Pydantic
SQLAlchemyDateTime = Annotated[py_datetime, None]

# Definição da classe Base para modelos SQLAlchemy
Base = declarative_base()

# --- Modelos SQLAlchemy ---

class User(Base):
    """Modelo de usuário do sistema"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

class SpotifyConfig(Base):
    """Configuração do Spotify para um usuário"""
    __tablename__ = "spotify_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    client_id = Column(String(100), nullable=False)
    client_secret = Column(String(100), nullable=False)
    redirect_uri = Column(String(255), nullable=False)
    download_path = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

class Download(Base):
    """Registro de downloads"""
    __tablename__ = "downloads"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    download_id = Column(String(36), index=True, unique=True, nullable=False)  # UUID como string
    spotify_id = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)  # track ou playlist
    name = Column(String(255), nullable=True)
    artist = Column(String(255), nullable=True)
    status = Column(String(20), nullable=False)  # na_fila, processando, concluido, erro, cancelado
    progress = Column(Float, default=0.0, nullable=False)
    file_path = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

# --- Esquemas Pydantic ---

class UserBase(BaseModel):
    """Esquema base para usuários"""
    username: str
    email: EmailStr
    
    model_config = {"from_attributes": True}

class UserCreate(UserBase):
    """Esquema para criação de usuários"""
    password: str

class UserUpdate(BaseModel):
    """Esquema para atualização de usuários"""
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    
    model_config = {"from_attributes": True}

class UserResponse(UserBase):
    """Esquema para resposta de usuários"""
    id: int
    is_active: bool
    is_admin: bool
    created_at: SQLAlchemyDateTime
    
    model_config = {"from_attributes": True}

class Token(BaseModel):
    """Esquema para token de acesso"""
    access_token: str
    token_type: str

class SpotifyConfigBase(BaseModel):
    """Esquema base para configuração do Spotify"""
    client_id: str
    client_secret: str
    redirect_uri: str = "http://127.0.0.1:8888/callback"
    download_path: str = "./downloads"
    
    model_config = {"from_attributes": True}

class SpotifyConfigCreate(SpotifyConfigBase):
    """Esquema para criação de configuração do Spotify"""
    pass

class SpotifyConfigResponse(SpotifyConfigBase):
    """Esquema para resposta de configuração do Spotify"""
    id: int
    user_id: int
    created_at: SQLAlchemyDateTime
    updated_at: SQLAlchemyDateTime
    
    model_config = {"from_attributes": True}

class SpotifyUrl(BaseModel):
    """Esquema para URL do Spotify"""
    url: str

class SpotifyId(BaseModel):
    """Esquema para ID do Spotify"""
    id: str
    type: str

class DownloadRequest(BaseModel):
    """Esquema para solicitação de download"""
    spotify_id: str
    type: str = "track"  # track ou playlist
    priority: int = Field(5, ge=1, le=10)  # 1-10, onde 1 é maior prioridade

class DownloadStatus(BaseModel):
    """Esquema para status de download"""
    status: str
    message: str
    download_id: str

class DownloadResponse(BaseModel):
    """Esquema para resposta de download"""
    id: int
    user_id: int
    download_id: str
    spotify_id: str
    type: str
    name: Optional[str] = None
    artist: Optional[str] = None
    status: str
    progress: float
    file_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: SQLAlchemyDateTime
    updated_at: SQLAlchemyDateTime
    
    model_config = {"from_attributes": True}

class SearchResult(BaseModel):
    """Esquema para resultado de pesquisa"""
    id: str
    name: str
    artist: Optional[str] = None
    type: str
    image_url: Optional[str] = None