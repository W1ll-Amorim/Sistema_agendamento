import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base


# 1. Puxa a URL do PostgreSQL injetada pelo Docker via .env
# Se não encontrar a variável no ambiente, usa o SQLite como fallback local
DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL") or os.getenv("DATABASE_URL") or "sqlite:///database/database.db"

# 2. O parâmetro connect_args só deve existir se a conexão for SQLite
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# 3. Cria a engine com a URL dinâmica
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