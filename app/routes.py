from fastapi import APIRouter

# Criando as variáveis que o main.py quer tanto!
auth_routes = APIRouter()
task_routes = APIRouter()

# Rotas de teste
@auth_routes.get("/auth")
def rota_auth():
    return {"mensagem": "Rota de usuarios ok!"}

@task_routes.get("/tasks")
def rota_tasks():
    return {"mensagem": "Rota de tarefas ok!"}