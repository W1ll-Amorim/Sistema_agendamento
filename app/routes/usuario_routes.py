from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.usuario_schema import UsuarioCreate, UsuarioResponse
from app.models.models import UsuarioEmpresa

router = APIRouter(prefix="/usuario_empresa", tags=["Usuario_Empresa"])

@router.post("/")
def criar_usuario(
        usuario: UsuarioCreate,

        db:Session = Depends(get_db)
):
    novo_usuario = UsuarioEmpresa(
        nome = usuario.nome,
        email = usuario.email,
        senha_hash = usuario.senha
    )
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    return novo_usuario

@router.get("/", response_model=list[UsuarioResponse])
def listar_usuarios(
    db: Session = Depends(get_db)
):
    usuarios = db.query(UsuarioEmpresa).all()  

    if not usuarios:
        raise HTTPException(status_code=404, detail="Nenhum usuário encontrado")
    return usuarios