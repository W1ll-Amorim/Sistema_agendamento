from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core import get_db

from app.models.models import OrdemServico
router = APIRouter(prefix="ordens", tags=["Ordens"])

@router.post ("/")
def criar_ordem(
    titulo: str,
    descricao: str,
    id_usuario: str,
    id_ativo: str,
    id_servico: str,
    db: Session = Depends(get_db)
):
    nova_ordem = OrdemServico(
        titulo = titulo,
        descricao = descricao,
        id_usuario = id_usuario,
        id_ativo = id_ativo,
        id_servico = id_servico,
        id_servico = id_servico
    )

    db.add(nova_ordem)
    db.commit()
    db.refresh(nova_ordem)
    
    return(nova_ordem)
    
