from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core import get_db

from app.models.models import TipoServico

router = APIRouter(prefix="/servicos", tags=["Servicos"])

@router.post("/")
def criar_servico(
    nome: str,
    descricao: str,
    db: Session = Depends(get_db)
):

    servico = TipoServico(
        nome=nome,
        descricao=descricao
    )

    db.add(servico)
    db.commit()
    db.refresh(servico)

    return {"msg": "Serviço criado"}