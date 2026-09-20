from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.usuario_schema import UsuarioCreate, UsuarioResponse, LoginSchema
from app.models.models import UsuarioEmpresa, TipoUsuario
from app.core.security import hash_senha, verificar_senha, criar_token, verificar_token
from typing import Optional

router = APIRouter(prefix="/usuario_empresa", tags=["Usuario_Empresa"])

# =====================================================================
# 1. DEPENDÊNCIAS DE AUTENTICAÇÃO E AUTORIZAÇÃO
# =====================================================================

def obter_usuario_logado(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> UsuarioEmpresa:
    """Extrai o token do Header, valida e retorna o usuário atual do banco de dados."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Token não fornecido ou formato inválido"
        )

    token = authorization.split(" ")[1]
    payload = verificar_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Token inválido ou expirado"
        )

    email = payload.get("sub")
    usuario = db.query(UsuarioEmpresa).filter(UsuarioEmpresa.email == email).first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Usuário não encontrado"
        )

    return usuario


def verificar_tecnico(usuario: UsuarioEmpresa = Depends(obter_usuario_logado)):
    """Verifica se o usuário logado possui a permissão (role) de Técnico."""
    if usuario.tipo != TipoUsuario.TECNICO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Acesso restrito. Privilégios de técnico necessários."
        )
    return usuario

# =====================================================================
# 2. ROTAS
# =====================================================================

@router.post("/cadastro", status_code=status.HTTP_201_CREATED)
def cadastro(
    usuario: UsuarioCreate,
    db: Session = Depends(get_db)
):  
    """Cria um novo usuário comum no sistema."""
    if usuario.senha != usuario.confirmar_senha:
        raise HTTPException(status_code=400, detail="As senhas não coincidem")

    if len(usuario.senha) < 6:
        raise HTTPException(status_code=400, detail="A senha deve ter no mínimo 6 caracteres")

    usuario_existente = db.query(UsuarioEmpresa).filter(
        UsuarioEmpresa.email == usuario.email
    ).first()

    if usuario_existente:
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    # O novo usuário recebe o tipo COMUM pelo default definido no model
    novo_usuario = UsuarioEmpresa(
        nome=usuario.nome,
        email=usuario.email,
        senha_hash=hash_senha(usuario.senha)
    )

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    # Retornamos os dados para o FastAPI formatar automaticamente
    return {
        "msg": "Usuário criado com sucesso", 
        "usuario": {
            "id_usuario": novo_usuario.id_usuario,
            "nome": novo_usuario.nome,
            "email": novo_usuario.email,
            "tipo": novo_usuario.tipo.value
        }
    }


@router.get("/usuarios", response_model=list[UsuarioResponse])
def listar_usuarios(
    usuario_atual: UsuarioEmpresa = Depends(verificar_tecnico), 
    db: Session = Depends(get_db)
):
    """Retorna todos os usuários (Acesso restrito apenas para Técnicos)."""
    usuarios = db.query(UsuarioEmpresa).all()  

    if not usuarios:
        raise HTTPException(status_code=404, detail="Nenhum usuário encontrado")
    return usuarios


@router.post("/login")
def login(dados: LoginSchema, db: Session = Depends(get_db)):
    """Valida as credenciais e retorna o Token JWT junto com os dados de acesso."""
    usuario = db.query(UsuarioEmpresa).filter(
        UsuarioEmpresa.email == dados.email
    ).first()

    if not usuario or not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Email ou senha inválidos"
        )

    token = criar_token({"sub": usuario.email})

    return {
        "access_token": token,
        "token_type": "bearer",
        "id_usuario": usuario.id_usuario,
        "nome": usuario.nome,
        "email": usuario.email,
        "tipo": usuario.tipo.value 
    }


@router.get("/me")
def dados_usuario_logado(
    usuario: UsuarioEmpresa = Depends(obter_usuario_logado)
):
    """Retorna os dados do próprio usuário que está logado usando o Token fornecido."""
    return {
        "nome": usuario.nome, 
        "email": usuario.email,
        "tipo": usuario.tipo.value
    }