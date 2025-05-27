"""
Spotify Downloader API - Educational Project
Copyright (c) 2025 https://github.com/gaab0418

This project is for educational purposes only.
Licensed under MIT License - see LICENSE file for details.


Conexão com o banco de dados
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

# Criar URL de conexão MySQL
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

# Criar engine de conexão
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    pool_pre_ping=True,
    pool_recycle=3600  # Reciclar conexões após 1 hora
)

# Criar factory de sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos declarativos
Base = declarative_base()

def get_db():
    """
    Gera uma sessão de banco de dados para uso em endpoints da API.
    Implementa o padrão de dependência para uso com FastAPI.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Inicializa o banco de dados, criando todas as tabelas definidas.
    """
    from models import Base, User, SpotifyConfig, Download
    
    # Criar tabelas se não existirem
    Base.metadata.create_all(bind=engine)
    
    # Verificar se existe usuário admin
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.is_admin == True).first()
        
        # Se não existir admin, criar um padrão
        if not admin:
            from auth import get_password_hash
            
            # Criar usuário admin padrão
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),  # Mudar após primeira execução!
                is_active=True,
                is_admin=True
            )
            
            db.add(admin_user)
            db.commit()
            
            print("Usuário admin criado com senha padrão 'admin123'. MUDE A SENHA APÓS PRIMEIRO LOGIN!")
    finally:
        db.close()