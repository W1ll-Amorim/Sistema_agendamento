from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core import get_db

from app.models.models import Historico
router = APIRouter(prefix = "/historico", tags=["Historico"])

@router.post("/")
def criar_historico(
    id_ordem_servico: str,
    acao: str,
    id_usuario: str,
    db: Session = Depends(get_db)
):
    novo_historico = Historico(
        id_ordem_servico = id_ordem_servico,
        acao = acao,
        id_usuario = id_usuario,
    )

    db.add = (novo_historico)
    db.commit()
    db.refresh(novo_historico)

    return novo_historico