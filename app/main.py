import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# ---------------------------------------------------------
# Importações de Banco de Dados, Segurança e Modelos
# ---------------------------------------------------------
from app.core.database import engine, Base, SessionLocal, ensure_migrations
from app.models.models import UsuarioEmpresa, TipoUsuario
from app.core.security import hash_senha  # Corrigido de obter_hash_senha para hash_senha

from app.scheduler.Scheduler import start_scheduler
from app.routes import (
    usuario_routes,
    agendamento_routes,
    ativo_routes,
    ordem_routes,
    historico_routes,
    servico_routes,
)

# ---------------------------------------------------------
# FUNÇÃO DE CRIAÇÃO DO ADMIN PADRÃO
# ---------------------------------------------------------
def inicializar_admin_padrao():
    db = SessionLocal()
    try:
        # Verifica se já existe algum administrador no sistema (corrigido para .ADMIN maiúsculo)
        admin_existente = db.query(UsuarioEmpresa).filter(UsuarioEmpresa.tipo == TipoUsuario.ADMIN).first()
        
        if not admin_existente:
            # Cria o Admin Master
            novo_admin = UsuarioEmpresa(
                nome="Administrador Padrão",
                email="admin@sistema.com",
                senha_hash=hash_senha("admin123"), # Usando a função de hash correta
                tipo=TipoUsuario.ADMIN
            )
            db.add(novo_admin)
            db.commit()
            print("✅ Conta de Administrador padrão criada com sucesso (admin@sistema.com / admin123).")
    except Exception as e:
        print(f"❌ Erro ao inicializar admin padrão: {e}")
    finally:
        db.close()

# ---------------------------------------------------------
# LIFESPAN (EVENTOS DE INICIALIZAÇÃO)
# ---------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Cria as tabelas do banco de dados caso não existam
    Base.metadata.create_all(bind=engine)

    # 2. Aplicar migrações simples (ex: adicionar colunas não existentes no SQLite)
    ensure_migrations()

    # 3. Inicializa o admin logo depois que o banco (e tabelas) estiverem prontos
    inicializar_admin_padrao()

    # 4. Inicia o agendador de tarefas
    start_scheduler()
    print("🚀 Scheduler e Banco de Dados iniciados com sucesso.")
    
    yield

    # SHUTDOWN
    print("🛑 Encerrando aplicação...")


app = FastAPI(lifespan=lifespan)

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------
# Inclusão de Rotas (API)
# ---------------------------------------------------------
app.include_router(usuario_routes.router) # A rota principal do usuário já gerencia o prefixo
app.include_router(agendamento_routes.router, prefix="/agendamentos")
app.include_router(servico_routes.router, prefix="/servicos")
app.include_router(ordem_routes.router, prefix="/ordens")
app.include_router(ativo_routes.router, prefix="/ativos")
app.include_router(historico_routes.router, prefix="/historico")

# ---------------------------------------------------------
# Static + Templates
# ---------------------------------------------------------
app.mount("/static", StaticFiles(directory=os.path.join(base_dir, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

# ---------------------------------------------------------
# Views (Telas)
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