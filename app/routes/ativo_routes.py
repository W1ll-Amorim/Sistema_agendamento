from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core import get_db

from app.models.models import Ativo
router = APIRouter(prefix="ativo", tags= ["Ativo"])

router.post("/")
def criar_ativo(
        nome: str,
        tipo: str,
        id_usuario: str,
        db: Session = Depends(get_db)
):
    ativo = Ativo (
        nome = nome,
        tipo = tipo,
        id_usuario = id_usuario,
    )
    db.add(ativo)
    db.commit()
    db.refresh(ativo)
    
    return(ativo)