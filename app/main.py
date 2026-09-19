import os

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager

# Importações de Banco de Dados e Segurança
from app.core.database import engine, Base, SessionLocal, ensure_migrations
from app.models.models import UsuarioEmpresa, TipoUsuario
from app.core.security import obter_hash_senha # Certifique-se de ter essa função criada no seu core/security.py

from app.scheduler.Scheduler import start_scheduler

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routes import usuario_routes
from app.routes import agendamento_routes
from app.routes import ativo_routes
from app.routes import ordem_routes
from app.routes import historico_routes
from app.routes import servico_routes

# ---------------------------------------------------------
# FUNÇÃO DE CRIAÇÃO DO ADMIN PADRÃO
# ---------------------------------------------------------
def inicializar_admin_padrao():
    db = SessionLocal()
    try:
        # Verifica se já existe algum administrador no sistema
        admin_existente = db.query(UsuarioEmpresa).filter(UsuarioEmpresa.tipo == TipoUsuario.admin).first()
        
        if not admin_existente:
            # Cria o Admin Master
            novo_admin = UsuarioEmpresa(
                nome="Administrador Padrão",
                email="admin@sistema.com",
                senha_hash=obter_hash_senha("admin123"), # Altere a senha se necessário
                tipo=TipoUsuario.admin
            )
            db.add(novo_admin)
            db.commit()
            print("Conta de Administrador padrão criada com sucesso (admin@sistema.com / admin123).")
    except Exception as e:
        print(f"Erro ao inicializar admin padrão: {e}")
    finally:
        db.close()

# ---------------------------------------------------------
# LIFESPAN (EVENTOS DE INICIALIZAÇÃO)
# ---------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    start_scheduler()
    print("Scheduler iniciado")
    
    # Inicializa o admin logo depois que o banco (e tabelas) estiver pronto
    inicializar_admin_padrao()

    yield

    # SHUTDOWN (opcional)
    print("Encerrando aplicação")

app = FastAPI(lifespan=lifespan)

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Cria as tabelas do banco de dados caso não existam
Base.metadata.create_all(bind=engine)

# Aplicar migrações simples (ex: adicionar colunas não existentes)
ensure_migrations()

# Inclusão de Rotas
app.include_router(usuario_routes.router) # Se for usar a rota de listagem/promoção de usuários, certifique-se de adicioná-la aqui ou dentro deste arquivo
app.include_router(agendamento_routes.router, prefix="/agendamentos")
app.include_router(servico_routes.router, prefix="/servicos")
app.include_router(ordem_routes.router, prefix="/ordens")
app.include_router(ativo_routes.router, prefix="/ativos")
app.include_router(historico_routes.router, prefix="/historico")

# Static + Templates
app.mount("/static", StaticFiles(directory=os.path.join(base_dir, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(base_dir,"templates"))

# Views
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