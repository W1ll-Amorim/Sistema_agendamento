#!/bin/sh
set -eu

echo "==> Aguardando conexão com o PostgreSQL..."

python - <<'PY'
import os
import sys
import time
import psycopg2

config = {
    "host": os.getenv("DB_HOST", "db"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.environ["DB_NAME"],
    "user": os.environ["DB_USER"],
    "password": os.environ["DB_PASSWORD"],
    "connect_timeout": 3,
}

for tentativa in range(1, 31):
    try:
        with psycopg2.connect(**config):
            pass

        print("==> PostgreSQL disponível!")
        break

    except psycopg2.OperationalError as erro:
        print(
            f"==> Tentativa {tentativa}/30: banco indisponível.",
            flush=True,
        )

        if tentativa == 30:
            print(f"ERRO: não foi possível conectar ao PostgreSQL: {erro}")
            sys.exit(1)

        time.sleep(2)
PY

echo "==> Aplicando migrations do Alembic..."
alembic upgrade head

echo "==> Iniciando FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000