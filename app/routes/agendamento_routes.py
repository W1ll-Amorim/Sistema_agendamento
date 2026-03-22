from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.models import Agendamento

router = APIRouter(prefix= "/agendamentos", tags=["Agendamentos"])

@router.post("/")
def criar_agendamento(
    id_ordem_servico: str,
    ir_usuario: str,
    db: Session = Depends(get_db)
):
    
    agendamento = Agendamento(
        id_ordem_servico = id_ordem_servico,
        id_usuario = id_usuario

    )