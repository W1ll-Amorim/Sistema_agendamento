from fastapi import FastAPI
from app.core.database import engine, Base


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