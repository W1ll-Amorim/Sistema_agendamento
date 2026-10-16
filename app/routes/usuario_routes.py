from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.schemas.usuario_schema import UsuarioCreate, UsuarioResponse, LoginSchema
from app.models.models import UsuarioEmpresa, TipoUsuario
from app.core.security import hash_senha, verificar_senha, criar_token, verificar_token
from app.core.deps import get_current_user, verificar_admin

router = APIRouter(prefix="/usuario_empresa", tags=["Usuario_Empresa"])

def _tipo_str(usuario: UsuarioEmpresa) -> str:
    """Normaliza o tipo do usuário para string maiúscula (COMUM/TECNICO/ADMIN)."""
    tipo = getattr(usuario, "tipo", None)
    if tipo is None:
        return "COMUM"
    if isinstance(tipo, TipoUsuario):
        return tipo.name  # COMUM, TECNICO, ADMIN
    return str(tipo).upper()

class AlterarTipoBody(BaseModel):
    tipo: str

@router.post("/cadastro")
def cadastro(usuario: UsuarioCreate, db: Session = Depends(get_db)):
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
        senha_hash=hash_senha(usuario.senha),
        tipo=TipoUsuario.COMUM,
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
            "tipo": _tipo_str(novo_usuario),
        },
    }

@router.get("/usuarios")
def listar_usuarios(
    db: Session = Depends(get_db),
    _admin: UsuarioEmpresa = Depends(verificar_admin),
):
    usuarios = db.query(UsuarioEmpresa).all()
    if not usuarios:
        raise HTTPException(status_code=404, detail="Nenhum usuário encontrado")

    return [
        {
            "id_usuario": u.id_usuario,
            "nome": u.nome,
            "email": u.email,
            "tipo": _tipo_str(u),
        }
        for u in usuarios
    ]

@router.post("/login")
def login(dados: LoginSchema, db: Session = Depends(get_db)):
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
        "tipo": _tipo_str(usuario),
    }

@router.get("/me")
def dados_usuario_logado(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Lista todos os usuarios.
    Acesso restrito apenas a ADMIN.
    Retorna lista plain dict para garantir o campo tipo.
    """
    usuarios = db.query(UsuarioEmpresa).all()
    
    if not authorization or " " not in authorization:
        raise HTTPException(status_code=401, detail="Token ausente ou mal formatado")

    token = authorization.split(" ", 1)[1]
    payload = verificar_token(token)

    return [
        {
            "id_usuario": str(u.id_usuario),
            "nome": u.nome,
            "email": u.email,
            "tipo": _tipo_str(u)
        }
        for u in usuarios
    ]

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
    
    # Executa a deleção
    db.delete(usuario)
    db.commit()

    return {
        "msg": "Usuário excluído com sucesso",
        "id_usuario": usuario.id_usuario,
        "nome": usuario.nome,
        "email": usuario.email,
        "tipo": _tipo_str(usuario),
    }

@router.put("/usuarios/{id_usuario}/tipo")
def alterar_tipo_usuario(
    id_usuario: str,
    body: AlterarTipoBody,
    db: Session = Depends(get_db),
    _admin: UsuarioEmpresa = Depends(verificar_admin),
):
    """ADMIN promove/rebaixa usuário entre COMUM e TECNICO."""
    novo = (body.tipo or "").strip().upper()
    mapa = {
        "COMUM": TipoUsuario.COMUM,
        "TECNICO": TipoUsuario.TECNICO,
    }
    if novo not in mapa:
        raise HTTPException(
            status_code=400,
            detail="Tipo inválido. Use COMUM ou TECNICO.",
        )

    alvo = db.query(UsuarioEmpresa).filter(
        UsuarioEmpresa.id_usuario == id_usuario
    ).first()
    if not alvo:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if _tipo_str(alvo) == "ADMIN":
        raise HTTPException(
            status_code=400,
            detail="Não é permitido alterar o tipo de um administrador por esta rota.",
        )

    try:
        alvo.tipo = mapa[novo]
        db.commit()
        db.refresh(alvo)
    except Exception as e:
        db.rollback()
        # Fallback SQLite TEXT / enum incompatível
        try:
            from sqlalchemy import text
            db.execute(
                text("UPDATE usuario_empresa SET tipo = :t WHERE id_usuario = :id"),
                {"t": mapa[novo].value, "id": id_usuario},
            )
            db.commit()
            alvo = db.query(UsuarioEmpresa).filter(
                UsuarioEmpresa.id_usuario == id_usuario
            ).first()
        except Exception as e2:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Erro ao alterar tipo: {e} | fallback: {e2}",
            )

    return {
        "msg": f"Tipo atualizado para {novo}",
        "id_usuario": alvo.id_usuario,
        "tipo": _tipo_str(alvo),
    }