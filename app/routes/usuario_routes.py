from fastapi import APIRouter, Depends, HTTPException, Header, status, Body
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.usuario_schema import UsuarioCreate, UsuarioResponse, LoginSchema
from app.models.models import UsuarioEmpresa, TipoUsuario
from app.core.security import hash_senha, verificar_senha, criar_token, verificar_token
from typing import Optional
from pydantic import BaseModel


router = APIRouter(prefix="/usuario_empresa", tags=["Usuario_Empresa"])


# =====================================================================
# SCHEMAS AUXILIARES
# =====================================================================

class AlterarTipoSchema(BaseModel):
    tipo: str  # "COMUM" | "TECNICO" | "ADMIN"


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


def _tipo_valor(tipo) -> str:
    """Normaliza tipo para string maiuscula (aceita enum ou str)."""
    if tipo is None:
        return ""
    if hasattr(tipo, "value"):
        return str(tipo.value).upper()
    if hasattr(tipo, "name"):
        return str(tipo.name).upper()
    return str(tipo).upper()


def verificar_admin(usuario: UsuarioEmpresa = Depends(obter_usuario_logado)):
    """Acesso restrito apenas a ADMIN."""
    if _tipo_valor(usuario.tipo) != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito. Privileges de administrador necessarios."
        )
    return usuario


def verificar_tecnico_ou_admin(usuario: UsuarioEmpresa = Depends(obter_usuario_logado)):
    """Acesso para TECNICO ou ADMIN."""
    if _tipo_valor(usuario.tipo) not in ("TECNICO", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito. Privileges de tecnico ou administrador necessarios."
        )
    return usuario


def verificar_tecnico(usuario: UsuarioEmpresa = Depends(obter_usuario_logado)):
    """TECNICO ou ADMIN."""
    if _tipo_valor(usuario.tipo) not in ("TECNICO", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito. Privileges de tecnico necessarios."
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

    # Novo usuário nasce como COMUM (default do model)
    novo_usuario = UsuarioEmpresa(
        nome=usuario.nome,
        email=usuario.email,
        senha_hash=hash_senha(usuario.senha)
    )

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    return {
        "msg": "Usuário criado com sucesso",
        "usuario": {
            "id_usuario": novo_usuario.id_usuario,
            "nome": novo_usuario.nome,
            "email": novo_usuario.email,
            "tipo": novo_usuario.tipo.value
        }
    }


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
        "id_usuario": str(usuario.id_usuario),
        "nome": usuario.nome,
        "email": usuario.email,
        "tipo": _tipo_valor(usuario.tipo)
    }


@router.get("/me")
def dados_usuario_logado(
    usuario: UsuarioEmpresa = Depends(obter_usuario_logado)
):
    """Retorna os dados do próprio usuário que está logado usando o Token fornecido."""
    return {
        "id_usuario": str(usuario.id_usuario),
        "nome": usuario.nome,
        "email": usuario.email,
        "tipo": _tipo_valor(usuario.tipo)
    }


@router.get("/usuarios")
def listar_usuarios(
    usuario_atual: UsuarioEmpresa = Depends(verificar_admin),
    db: Session = Depends(get_db)
):
    """
    Lista todos os usuarios.
    Acesso restrito apenas a ADMIN.
    Retorna lista plain dict para garantir o campo tipo.
    """
    usuarios = db.query(UsuarioEmpresa).all()

    if not usuarios:
        raise HTTPException(status_code=404, detail="Nenhum usuario encontrado")

    return [
        {
            "id_usuario": str(u.id_usuario),
            "nome": u.nome,
            "email": u.email,
            "tipo": _tipo_valor(u.tipo)
        }
        for u in usuarios
    ]


@router.put("/{id_usuario}/tipo")
def alterar_tipo_usuario(
    id_usuario: str,
    dados: AlterarTipoSchema,
    usuario_atual: UsuarioEmpresa = Depends(verificar_admin),
    db: Session = Depends(get_db)
):
    """
    Altera o tipo (perfil) de um usuário.
    Apenas ADMIN. Tipos permitidos: COMUM ou TECNICO.
    """
    tipo_str = str(dados.tipo or "").strip().upper()

    # Aceita COMUM/TECNICO e tambem valores em minusculo do enum
    mapa = {
        "COMUM": TipoUsuario.COMUM,
        "TECNICO": TipoUsuario.TECNICO,
        "COMUM".lower(): TipoUsuario.COMUM,
        "TECNICO".lower(): TipoUsuario.TECNICO,
    }
    # normaliza chave
    if tipo_str not in ("COMUM", "TECNICO"):
        raise HTTPException(
            status_code=400,
            detail="Tipo invalido. O administrador so pode definir: COMUM ou TECNICO."
        )

    usuario = db.query(UsuarioEmpresa).filter(
        UsuarioEmpresa.id_usuario == str(id_usuario)
    ).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")

    if str(usuario.id_usuario) == str(usuario_atual.id_usuario):
        raise HTTPException(
            status_code=400,
            detail="Voce nao pode alterar o proprio perfil por esta tela."
        )

    if _tipo_valor(usuario.tipo) == "ADMIN":
        raise HTTPException(
            status_code=400,
            detail="Nao e permitido alterar o perfil de outro administrador."
        )

    novo_enum = mapa[tipo_str]
    usuario.tipo = novo_enum
    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    # Confirma se gravou; se o ORM nao refletir, tenta update direto
    tipo_retorno = _tipo_valor(usuario.tipo)
    if tipo_retorno not in ("COMUM", "TECNICO") or tipo_retorno != tipo_str:
        db.query(UsuarioEmpresa).filter(
            UsuarioEmpresa.id_usuario == str(id_usuario)
        ).update({"tipo": novo_enum})
        db.commit()
        usuario = db.query(UsuarioEmpresa).filter(
            UsuarioEmpresa.id_usuario == str(id_usuario)
        ).first()
        tipo_retorno = _tipo_valor(usuario.tipo) if usuario else tipo_str

    return {
        "msg": f"Usuario atualizado para {tipo_retorno}",
        "usuario": {
            "id_usuario": str(usuario.id_usuario),
            "nome": usuario.nome,
            "email": usuario.email,
            "tipo": tipo_retorno
        }
    }


@router.delete("/{id_usuario}")
def excluir_usuario(
    id_usuario: str,
    usuario_atual: UsuarioEmpresa = Depends(verificar_admin),
    db: Session = Depends(get_db)
):
    """
    Exclui um usuário do sistema.
    Apenas ADMIN. Não permite excluir a si mesmo nem outro ADMIN.
    """
    usuario = db.query(UsuarioEmpresa).filter(
        UsuarioEmpresa.id_usuario == id_usuario
    ).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if usuario.id_usuario == usuario_atual.id_usuario:
        raise HTTPException(
            status_code=400,
            detail="Você não pode excluir a própria conta."
        )

    if _tipo_valor(usuario.tipo) == "ADMIN":
        raise HTTPException(
            status_code=400,
            detail="Não é permitido excluir outro administrador."
        )

    db.delete(usuario)
    db.commit()

    return {
        "msg": "Usuário excluído com sucesso",
        "id_usuario": id_usuario
    }
