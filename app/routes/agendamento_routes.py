from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core import get_db
from datetime import datetime
from app.models.models import Agendamento
from app.scheduler import agendar_ordem



router = APIRouter(prefix= "/agendamentos", tags=["Agendamentos"])

@router.post("/")
def criar_agendamento(
    id_ordem_servico: str,
    id_usuario: str,
    data_agendamento: datetime,

    db: Session = Depends(get_db)
):
    
    agendamento = Agendamento(
        id_ordem_servico = id_ordem_servico,
        id_usuario = id_usuario,
        data_agendamento = data_agendamento

    )

    db.add(agendamento)
    db.commit()
    db.refresh(agendamento)

    agendar_ordem(data_agendamento, id_ordem_servico)

    return agendamento