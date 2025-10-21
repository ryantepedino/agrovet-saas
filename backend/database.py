from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Usa SQLite local por padrão, mas aceita PostgreSQL via variável de ambiente
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./agrovet.db")

# Configura o engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

# Cria a sessão de conexão
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Base para os modelos ORM
Base = declarative_base()
