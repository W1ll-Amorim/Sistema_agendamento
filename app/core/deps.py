from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verificar_token
from app.models.models import UsuarioEmpresa, TipoUsuario


def _norm_tipo(usuario: UsuarioEmpresa) -> str:
    """Retorna COMUM | TECNICO | ADMIN independente de enum/string no banco."""
    tipo = getattr(usuario, "tipo", None)
    if tipo is None:
        return "COMUM"
    if isinstance(tipo, TipoUsuario):
        return tipo.name  # COMUM, TECNICO, ADMIN
    s = str(tipo).strip()
    # aceita value ("comum") ou name ("COMUM")
    upper = s.upper()
    if upper in ("COMUM", "TECNICO", "ADMIN"):
        return upper
    lower_map = {"comum": "COMUM", "tecnico": "TECNICO", "admin": "ADMIN"}
    return lower_map.get(s.lower(), "COMUM")


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> UsuarioEmpresa:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido ou formato inválido",
        )
    token = authorization.split(" ", 1)[1]
    payload = verificar_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )
    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sem identificação de usuário",
        )
    usuario = db.query(UsuarioEmpresa).filter(UsuarioEmpresa.email == email).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário do token não encontrado",
        )
    return usuario


def verificar_tecnico_ou_admin(
    usuario: UsuarioEmpresa = Depends(get_current_user),
) -> UsuarioEmpresa:
    if _norm_tipo(usuario) not in ("TECNICO", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito. Privilégios de técnico ou admin necessários.",
        )
    return usuario


def verificar_admin(
    usuario: UsuarioEmpresa = Depends(get_current_user),
) -> UsuarioEmpresa:
    if _norm_tipo(usuario) != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores.",
        )
    return usuario
