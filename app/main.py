import os
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI,APIRouter, Request, Depends, Query
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.database import engine, Base, SessionLocal, get_db
from sqlalchemy.orm import Session
from app.models.models import UsuarioEmpresa, TipoUsuario, OrdemServico
from app.core.security import hash_senha

from app.core.deps import get_current_user, _norm_tipo

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

router = APIRouter()

@router.get("/")
def listar_agendamentos(
    setor: Optional[str] = Query(None, description="Filtro por setor"),
    status: Optional[str] = Query(None, description="Filtro por status"),
    prioridade: Optional[str] = Query(None, description="Filtro por prioridade"),
    db: Session = Depends(get_db),
    usuario_logado = Depends(get_current_user)  # 🔒 Autentica e bloqueia acessos sem token
):
    # 1. Inicia a query base buscando as ordens de serviço (agendamentos)
    query = db.query(OrdemServico)
    
    # 2. Trava de Segurança (Zero Trust)
    tipo_usuario = _norm_tipo(usuario_logado)
    
    if tipo_usuario == "COMUM":
        # Se for COMUM, injeta o filtro obrigatório amarrando ao ID do usuário do token.
        # (Se na sua model OrdemServico a coluna for 'id_usuario', mantenha assim. 
        #  Se a chave primária em UsuarioEmpresa for 'id', use usuario_logado.id)
        query = query.filter(OrdemServico.id_usuario == usuario_logado.id)
    
    # 3. Filtros Dinâmicos do Frontend
    # Ignora o valor "all" que é enviado quando o usuário seleciona "Todos" no dropdown
    if setor and setor.lower() != "all":
        # Ajuste o atributo abaixo conforme sua model (ex: OrdemServico.setor)
        query = query.filter(OrdemServico.descricao_servico == setor)
        
    if status and status.lower() != "all":
        query = query.filter(OrdemServico.status == status)
        
    if prioridade and prioridade.lower() != "all":
        # Ajuste o atributo abaixo conforme sua model (ex: OrdemServico.criticidade)
        query = query.filter(OrdemServico.prioridade == prioridade)
        
    # 4. Executa a busca no banco de dados
    resultados = query.all()
    
    # 5. Retorna o JSON no padrão esperado pela função carregarAgendamentos() do seu frontend
    return {"agendamentos": resultados}