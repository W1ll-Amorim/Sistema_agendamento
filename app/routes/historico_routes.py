from fastapi import APIRouter, Depends, HTTPException, Query, Header, Body
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verificar_token
from app.models.models import Historico, UsuarioEmpresa

router = APIRouter(prefix="", tags=["Historico"])


# Dependência para checar token (vinda da sua máquina local)
def get_current_user(authorization: str = Header(None)):
    if not authorization:
        return None
    if not authorization.startswith("Bearer "):
        return None
    token = authorization.replace("Bearer ", "")
    payload = verificar_token(token)
    return payload


@router.post("/")
def criar_historico(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: dict | None = Depends(get_current_user)
):
    try:
        id_ordem_servico = payload.get('id_ordem_servico')
        observacao = payload.get('observacao')
        id_usuario = payload.get('id_usuario')

        if not id_ordem_servico or not observacao or not id_usuario:
            return {"error": "Campos obrigatórios: id_ordem_servico, observacao, id_usuario"}

        novo_historico = Historico(
            id_ordem_servico=id_ordem_servico,
            acao="comentario",
            observacao=observacao,
            id_usuario=id_usuario
        )

        db.add(novo_historico)
        db.commit()
        db.refresh(novo_historico)

        return {
            "message": "Comentário criado",
            "historico": {
                "id_historico": novo_historico.id_historico,
                "data_registro": novo_historico.data_registro.isoformat(),
                "observacao": novo_historico.observacao,
                "id_usuario": novo_historico.id_usuario
            }
        }
    except Exception as e:
        db.rollback()
        return {"error": str(e)}


@router.get("/")
def listar_historico(id_ordem_servico: str = Query(...), db: Session = Depends(get_db)):
    try:
        registros = db.query(Historico).filter(Historico.id_ordem_servico == id_ordem_servico).order_by(Historico.data_registro).all()
        resultado = []
        for r in registros:
            usuario = db.query(UsuarioEmpresa).filter(UsuarioEmpresa.id_usuario == r.id_usuario).first()
            resultado.append({
                "id_historico": r.id_historico,
                "data_registro": r.data_registro.isoformat(),
                "observacao": r.observacao,
                "id_usuario": r.id_usuario,
                "nome_usuario": usuario.nome if usuario else None
            })
        return {"historicos": resultado}
    except Exception as e:
        return {"error": str(e)}