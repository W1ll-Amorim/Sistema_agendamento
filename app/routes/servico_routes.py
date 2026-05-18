from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.database import get_db

from app.models.models import TipoServico

router = APIRouter(prefix="/servicos", tags=["Servicos"])

@router.post("/")
def criar_servico(
    nome: str,
    descricao: str,
    db: Session = Depends(get_db)
):

    novo_servico = TipoServico(
        nome=nome,
        descricao=descricao
    )

    db.add(novo_servico)
    db.commit()
    db.refresh(novo_servico)

    return {"msg": "Serviço criado"}