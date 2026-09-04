import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Removido connect_args={"check_same_thread": False}
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_migrations():
    """Aplica migrações simples necessárias no banco SQLite (não usa Alembic).
    Atualmente garante que a coluna 'prioridade' exista em 'ordem_servico'.
    """
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