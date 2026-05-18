from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
<<<<<<< HEAD
=======
from sqlalchemy import text
>>>>>>> 90eb54dae882f9d8128c746bb2e118408616fb41

DATABASE_URL = "sqlite:///database/database.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
<<<<<<< HEAD
        db.close()
=======
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
>>>>>>> 90eb54dae882f9d8128c746bb2e118408616fb41
