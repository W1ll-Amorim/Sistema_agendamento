from fastapi import APIRouter, Depends
from sqlalchemy.orm import session
from datetime import datetime

from app.database import SessionLocal
from app.models import Tasks

router = APIRouter()

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.closed()

@router.post("/tasks")

def nova_tarefa(




):