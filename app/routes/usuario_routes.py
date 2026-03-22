from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core import get_db

from app.models.models import UsuarioEmpresa
router = APIRouter(prefix="usuario_empresa", tags=["Usuario_Empresa"])

router.post("/")
def criar_usuario(
        nome: str,
        email: str,
        senha: str,

        db:Session = Depends(get_db)
):
    usuario = UsuarioEmpresa(
        nome = nome,
        email = email,
        senha_hash = senha,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)

@router.get("/")
def listar_usuarios(
    db: Session = Depends(get_db)
):
  return db.query(UsuarioEmpresa).all()  
