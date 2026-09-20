import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Tenta obter a URL completa pelas variáveis de ambiente
DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL") or os.getenv("DATABASE_URL")

# 2. Se não encontrou a URL completa, tenta montar com as variáveis do Docker (branch main)
if not DATABASE_URL:
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST", "db")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME")
    
    # Se tiver as credenciais do Postgres, monta a URL
    if DB_USER and DB_PASSWORD and DB_NAME:
        DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        # Fallback para o SQLite (branch lohan) para rodar localmente sem Docker
        DATABASE_URL = "sqlite:///database/database.db"

# 3. O parâmetro connect_args só deve existir se a conexão for SQLite
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# 4. Cria a engine
engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def ensure_migrations():
    """Garante migrações básicas caso o projeto rode em ambiente SQLite local sem Alembic."""
    if not DATABASE_URL.startswith("sqlite"):
        # No PostgreSQL, as migrações são controladas pelo Alembic
        return

    conn = engine.connect()
    try:
        try:
            res = conn.execute(text("PRAGMA table_info('ordem_servico')"))
            cols = [row[1] for row in res.fetchall()]
        except Exception:
            cols = []

        if 'prioridade' not in cols:
            try:
                conn.execute(text("ALTER TABLE ordem_servico ADD COLUMN prioridade TEXT"))
                print("Migration: coluna 'prioridade' adicionada em ordem_servico")
            except Exception as e:
                print("Falha ao aplicar migration 'prioridade':", e)
    finally:
        conn.close()