from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.usuario_schema import UsuarioCreate, UsuarioResponse
from app.models.models import UsuarioEmpresa
from app.core.security import hash_senha
from app.core.security import verificar_senha, criar_token

router = APIRouter(prefix="/usuario_empresa", tags=["Usuario_Empresa"])

@router.post("/cadastro")
def cadastro(
    usuario: UsuarioCreate,
    db: Session = Depends(get_db)
):  
    usuario_existente = db.query(UsuarioEmpresa).filter(
        UsuarioEmpresa.email == usuario.email
    ).first()

    if usuario_existente:
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    novo_usuario = UsuarioEmpresa(
        nome=usuario.nome,
        email=usuario.email,
        senha_hash=hash_senha(usuario.senha ) # ⚠️ depois vamos criptografar isso
    )

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    return {"msg": "Usuário criado com sucesso"}

@router.get("/usuarios", response_model=list[UsuarioResponse])
def listar_usuarios(
    db: Session = Depends(get_db)
):
    usuarios = db.query(UsuarioEmpresa).all()  

    if not usuarios:
        raise HTTPException(status_code=404, detail="Nenhum usuário encontrado")
    return usuarios

@router.post("/login")
def login(dados: LoginSchema, db: Session = Depends(get_db)):

    usuario = db.query(UsuarioEmpresa).filter(
        UsuarioEmpresa.email == dados.email
    ).first()

    if not usuario:
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")

    if not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")

    token = criar_token({"sub": usuario.email})

    return {
        "access_token": token,
        "token_type": "bearer"
    }