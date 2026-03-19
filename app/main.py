from fastapi import FastAPI
from database import engine
import models

# Puxando as rotas limpas do arquivo routes.py
from routes import auth_routes
from routes import task_routes

app = FastAPI()

# Criando as tabelas no banco de dados
models.Base.metadata.create_all(bind=engine)

# Conectando as rotas ao aplicativo
app.include_router(auth_routes)
app.include_router(task_routes)