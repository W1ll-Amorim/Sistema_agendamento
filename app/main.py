from fastapi import FastAPI
from database import engine
import models

from app.routes import auth_routes
from app.routes import task_routes

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

app.include_router(auth_routes.router)
app.include_router(task_routes.router)