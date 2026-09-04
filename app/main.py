import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.scheduler.Scheduler import start_scheduler
from app.routes import (
    usuario_routes,
    agendamento_routes,
    ativo_routes,
    ordem_routes,
    historico_routes,
    servico_routes,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    start_scheduler()
    print("Scheduler iniciado")

    yield

    # SHUTDOWN
    print("Encerrando aplicação")


app = FastAPI(lifespan=lifespan)

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Rotas da API
app.include_router(usuario_routes.router)
app.include_router(agendamento_routes.router, prefix="/agendamentos")
app.include_router(servico_routes.router, prefix="/servicos")
app.include_router(ordem_routes.router, prefix="/ordens")
app.include_router(ativo_routes.router, prefix="/ativos")
app.include_router(historico_routes.router, prefix="/historico")

# Static + Templates
app.mount("/static", StaticFiles(directory=os.path.join(base_dir, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

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