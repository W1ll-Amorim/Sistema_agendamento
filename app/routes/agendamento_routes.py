from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core import get_db
from app.models.models import Agendamento



router = APIRouter(prefix= "/agendamentos", tags=["Agendamentos"])

@router.post("/")
def criar_agendamento(
    id_ordem_servico: str,
    id_usuario: str,
    db: Session = Depends(get_db)
):
    
    agendamento = Agendamento(
        id_ordem_servico = id_ordem_servico,
        id_usuario = id_usuario

    )

    db.add(agendamento)
    db.commit()
    db.refresh(agendamento)

    return agendamento