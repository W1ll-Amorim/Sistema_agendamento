import os
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request
from app.core.database import engine, Base
from app.scheduler import Scheduler

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routes import usuario_routes
from app.routes import agendamento_routes
from app.routes import ativo_routes
from app.routes import ordem_routes
from app.routes import historico_routes
from app.routes import servico_routes

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(usuario_routes.router)
app.include_router(agendamento_routes.router)
app.include_router(servico_routes.router)
app.include_router(ordem_routes.router)
app.include_router(ativo_routes.router)
app.include_router(historico_routes.router)

# Esta linha é a "mágica" que faz o CSS funcionar

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/index")
async def read_cadastro(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/cadastro")
async def read_cadastro(request: Request):
    return templates.TemplateResponse("cadastro.html", {"request": request})

@app.get("/telainicial")
async def read_cadastro(request: Request):
    return templates.TemplateResponse("telainicial.html", {"request": request})
