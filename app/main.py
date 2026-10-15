import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.database import engine, Base, SessionLocal
from app.models.models import UsuarioEmpresa, TipoUsuario
from app.core.security import hash_senha
from app.scheduler.Scheduler import start_scheduler, stop_scheduler
from app.routes import (
    usuario_routes, agendamento_routes, ativo_routes,
    ordem_routes, historico_routes, servico_routes,
)

DATABASE_URL = os.getenv("DATABASE_URL", "")


def inicializar_admin_padrao():
    db = SessionLocal()
    try:
        admin = (
            db.query(UsuarioEmpresa)
            .filter(UsuarioEmpresa.tipo == TipoUsuario.ADMIN)
            .first()
        )
        if not admin:
            db.add(UsuarioEmpresa(
                nome="Administrador Padrão",
                email="admin@sistema.com",
                senha_hash=hash_senha("admin123"),
                tipo=TipoUsuario.ADMIN,
            ))
            db.commit()
            print("Admin padrao criado (admin@sistema.com / admin123).")
    except Exception as e:
        print(f"Erro ao inicializar admin: {e}")
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Postgres: schema so via Alembic (nao usa create_all)
    # SQLite local (dev sem Docker): pode criar tabelas
    if DATABASE_URL.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)

    inicializar_admin_padrao()
    start_scheduler()
    print("App iniciado.")
    yield
    stop_scheduler()
    print("App encerrado.")


app = FastAPI(lifespan=lifespan)
# ... resto igual (routers, static, templates)

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------
# Rotas da API
# ---------------------------------------------------------
app.include_router(usuario_routes.router)  # prefix interno: /usuario_empresa
app.include_router(agendamento_routes.router, prefix="/agendamentos")
app.include_router(servico_routes.router, prefix="/servicos")
app.include_router(ordem_routes.router, prefix="/ordens")
app.include_router(ativo_routes.router, prefix="/ativos")
app.include_router(historico_routes.router, prefix="/historico")


# ---------------------------------------------------------
# Static + Templates
# ---------------------------------------------------------
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(base_dir, "static")),
    name="static",
)
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))


# ---------------------------------------------------------
# Views (telas HTML)
# ---------------------------------------------------------
@app.get("/")
def root():
    return RedirectResponse(url="/index")


@app.get("/index")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/cadastro")
async def cadastro(request: Request):
    return templates.TemplateResponse("cadastro.html", {"request": request})


@app.get("/telainicial")
async def telainicial(request: Request):
    return templates.TemplateResponse("telainicial.html", {"request": request})