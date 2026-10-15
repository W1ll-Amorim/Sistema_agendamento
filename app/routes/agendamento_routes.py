from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verificar_token
from datetime import datetime
from app.models.models import (
    Agendamento, OrdemServico, Ativo, TipoServico,
    UsuarioEmpresa, TipoUsuario
)
from app.schemas.agendamento_schema import AgendamentoCreate
from typing import Optional

try:
    from app.scheduler.Scheduler import agendar_ordem
except Exception:
    def agendar_ordem(*args, **kwargs):
        pass


router = APIRouter(prefix="", tags=["Agendamentos"])


def obter_usuario_completo(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> UsuarioEmpresa:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido ou formato inválido")

    token = authorization.split(" ")[1]
    payload = verificar_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

    email = payload.get("sub")
    usuario = db.query(UsuarioEmpresa).filter(UsuarioEmpresa.email == email).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return usuario


def _tipo_val(tipo) -> str:
    if tipo is None:
        return ""
    if hasattr(tipo, "value"):
        return str(tipo.value).upper()
    if hasattr(tipo, "name"):
        return str(tipo.name).upper()
    return str(tipo).upper()


def _is_admin(u: UsuarioEmpresa) -> bool:
    return _tipo_val(u.tipo) == "ADMIN"


def _is_tecnico(u: UsuarioEmpresa) -> bool:
    return _tipo_val(u.tipo) == "TECNICO"


def _is_comum(u: UsuarioEmpresa) -> bool:
    return _tipo_val(u.tipo) == "COMUM"


def _mesmo_usuario(id_a, id_b) -> bool:
    return str(id_a) == str(id_b)


@router.post("/")
def criar_agendamento_completo(
    agendamento_data: AgendamentoCreate,
    db: Session = Depends(get_db),
    usuario: UsuarioEmpresa = Depends(obter_usuario_completo)
):
    """TECNICO nao cria. COMUM e ADMIN podem."""
    if _is_tecnico(usuario):
        raise HTTPException(status_code=403, detail="Tecnicos nao podem criar novas tarefas.")

    try:
        if _is_comum(usuario):
            id_dono = str(usuario.id_usuario)
        else:
            id_dono = str(getattr(agendamento_data, "id_usuario", None) or usuario.id_usuario)

        # setor vem em descricao_servico (front). Usamos como nome do servico
        # para o filtro de setor funcionar de forma confiavel.
        setor = (getattr(agendamento_data, "descricao_servico", None) or "").strip()
        nome_servico = setor or getattr(agendamento_data, "nome_servico", None) or "Geral"
        descricao_servico = setor or getattr(agendamento_data, "nome_servico", None) or ""

        servico = db.query(TipoServico).filter(TipoServico.nome == nome_servico).first()
        if not servico:
            servico = TipoServico(nome=nome_servico, descricao=descricao_servico)
            db.add(servico)
            db.flush()
        elif setor and (not servico.descricao or servico.descricao != setor):
            servico.descricao = setor
            db.flush()

        nome_ativo = getattr(agendamento_data, "nome_ativo", None) or "Geral"
        tipo_ativo = getattr(agendamento_data, "tipo_ativo", None) or "Equipamento"

        ativo = db.query(Ativo).filter(
            Ativo.nome == nome_ativo,
            Ativo.id_usuario == id_dono
        ).first()
        if not ativo:
            ativo = Ativo(nome=nome_ativo, tipo=tipo_ativo, id_usuario=id_dono)
            db.add(ativo)
            db.flush()

        criticidade = (
            getattr(agendamento_data, "criticidade", None)
            or getattr(agendamento_data, "prioridade", None)
            or "Alta"
        )

        nova_ordem = OrdemServico(
            titulo=agendamento_data.titulo,
            descricao=getattr(agendamento_data, "descricao", None) or agendamento_data.titulo,
            id_usuario=id_dono,
            id_ativo=ativo.id_ativo,
            id_servico=servico.id_servico,
            prioridade=str(criticidade),
            status=getattr(agendamento_data, "status", None) or "Pendente"
        )
        db.add(nova_ordem)
        db.flush()

        data_ag = agendamento_data.data_agendamento
        if isinstance(data_ag, str):
            data_ag = datetime.fromisoformat(data_ag.replace("Z", "+00:00"))

        status_ag = getattr(agendamento_data, "status", None) or "Pendente"

        novo_agendamento = Agendamento(
            id_ordem_servico=nova_ordem.id_ordem_servico,
            id_usuario=id_dono,
            data_agendamento=data_ag,
            status=status_ag
        )
        db.add(novo_agendamento)
        db.commit()
        db.refresh(novo_agendamento)
        db.refresh(nova_ordem)

        try:
            agendar_ordem(data_ag, nova_ordem.id_ordem_servico)
        except Exception:
            pass

        return {
            "message": "Agendamento criado com sucesso",
            "agendamento": {
                "id_agendamento": novo_agendamento.id_agendamento,
                "id_ordem_servico": nova_ordem.id_ordem_servico,
                "titulo": nova_ordem.titulo,
                "data_agendamento": novo_agendamento.data_agendamento.isoformat() if novo_agendamento.data_agendamento else None,
                "status": novo_agendamento.status,
                "id_usuario": id_dono
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao criar agendamento: {str(e)}")


@router.get("/")
def listar_agendamentos(
    id_usuario: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    usuario: UsuarioEmpresa = Depends(obter_usuario_completo)
):
    try:
        query = db.query(Agendamento)

        if _is_comum(usuario):
            query = query.filter(Agendamento.id_usuario == str(usuario.id_usuario))
        elif id_usuario:
            query = query.filter(Agendamento.id_usuario == str(id_usuario))

        agendamentos = query.order_by(Agendamento.data_agendamento.desc()).all()

        resultado = []
        for ag in agendamentos:
            ordem = db.query(OrdemServico).filter(
                OrdemServico.id_ordem_servico == ag.id_ordem_servico
            ).first()

            ativo = None
            servico = None
            if ordem:
                ativo = db.query(Ativo).filter(Ativo.id_ativo == ordem.id_ativo).first()
                servico = db.query(TipoServico).filter(
                    TipoServico.id_servico == ordem.id_servico
                ).first()

            # Setor = nome do servico (gravado a partir do setor do form)
            setor = ""
            if servico:
                setor = (servico.nome or servico.descricao or "").strip()
            if not setor:
                setor = "Geral"

            prioridade = ""
            if ordem and ordem.prioridade:
                prioridade = str(ordem.prioridade).strip()
            if not prioridade:
                prioridade = "Alta"

            status_val = (ag.status or "Pendente").strip()

            resultado.append({
                "id_agendamento": ag.id_agendamento,
                "titulo": (ordem.titulo if ordem else None) or "Sem titulo",
                "descricao": (ordem.descricao if ordem else None) or "",
                "nome_ativo": ativo.nome if ativo else "Geral",
                "tipo_ativo": ativo.tipo if ativo else "",
                "nome_servico": servico.nome if servico else "",
                "descricao_servico": setor,
                "data_agendamento": ag.data_agendamento.isoformat() if ag.data_agendamento else None,
                "id_ordem_servico": ag.id_ordem_servico,
                "status": status_val,
                "criticidade": prioridade,
                "id_usuario": ag.id_usuario
            })

        return {"agendamentos": resultado}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar agendamentos: {str(e)}")


@router.delete("/{id_agendamento}")
def deletar_agendamento(
    id_agendamento: str,
    db: Session = Depends(get_db),
    usuario: UsuarioEmpresa = Depends(obter_usuario_completo)
):
    try:
        agendamento = db.query(Agendamento).filter(
            Agendamento.id_agendamento == id_agendamento
        ).first()

        if not agendamento:
            raise HTTPException(status_code=404, detail="Agendamento nao encontrado")

        if _is_comum(usuario) and not _mesmo_usuario(agendamento.id_usuario, usuario.id_usuario):
            raise HTTPException(status_code=403, detail="Voce so pode excluir suas proprias tarefas.")

        db.delete(agendamento)
        db.commit()
        return {"message": "Agendamento deletado com sucesso"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao deletar: {str(e)}")


@router.put("/{id_agendamento}/status")
def atualizar_status_agendamento(
    id_agendamento: str,
    novo_status: str = Query(...),
    db: Session = Depends(get_db),
    usuario: UsuarioEmpresa = Depends(obter_usuario_completo)
):
    try:
        agendamento = db.query(Agendamento).filter(
            Agendamento.id_agendamento == id_agendamento
        ).first()

        if not agendamento:
            raise HTTPException(status_code=404, detail="Agendamento nao encontrado")

        if _is_comum(usuario) and not _mesmo_usuario(agendamento.id_usuario, usuario.id_usuario):
            raise HTTPException(status_code=403, detail="Voce so pode alterar suas proprias tarefas.")

        agendamento.status = novo_status
        db.commit()
        db.refresh(agendamento)
        return {"message": "Status atualizado com sucesso", "novo_status": novo_status}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar status: {str(e)}")


@router.put("/{id_agendamento}")
def atualizar_agendamento(
    id_agendamento: str,
    agendamento_data: AgendamentoCreate,
    db: Session = Depends(get_db),
    usuario: UsuarioEmpresa = Depends(obter_usuario_completo)
):
    try:
        agendamento = db.query(Agendamento).filter(
            Agendamento.id_agendamento == id_agendamento
        ).first()

        if not agendamento:
            raise HTTPException(status_code=404, detail="Agendamento nao encontrado")

        if _is_comum(usuario) and not _mesmo_usuario(agendamento.id_usuario, usuario.id_usuario):
            raise HTTPException(status_code=403, detail="Voce so pode editar suas proprias tarefas.")

        # setor vem em descricao_servico (front). Usamos como nome do servico
        # para o filtro de setor funcionar de forma confiavel.
        setor = (getattr(agendamento_data, "descricao_servico", None) or "").strip()
        nome_servico = setor or getattr(agendamento_data, "nome_servico", None) or "Geral"
        descricao_servico = setor or getattr(agendamento_data, "nome_servico", None) or ""

        servico = db.query(TipoServico).filter(TipoServico.nome == nome_servico).first()
        if not servico:
            servico = TipoServico(nome=nome_servico, descricao=descricao_servico)
            db.add(servico)
            db.flush()
        elif setor and (not servico.descricao or servico.descricao != setor):
            servico.descricao = setor
            db.flush()

        nome_ativo = getattr(agendamento_data, "nome_ativo", None) or "Geral"
        tipo_ativo = getattr(agendamento_data, "tipo_ativo", None) or "Equipamento"
        id_dono = str(getattr(agendamento_data, "id_usuario", None) or agendamento.id_usuario)

        ativo = db.query(Ativo).filter(
            Ativo.nome == nome_ativo,
            Ativo.id_usuario == id_dono
        ).first()
        if not ativo:
            ativo = Ativo(nome=nome_ativo, tipo=tipo_ativo, id_usuario=id_dono)
            db.add(ativo)
            db.flush()

        criticidade = (
            getattr(agendamento_data, "criticidade", None)
            or getattr(agendamento_data, "prioridade", None)
        )

        ordem = db.query(OrdemServico).filter(
            OrdemServico.id_ordem_servico == agendamento.id_ordem_servico
        ).first()

        if ordem:
            ordem.titulo = agendamento_data.titulo
            ordem.descricao = getattr(agendamento_data, "descricao", None) or agendamento_data.titulo
            ordem.id_ativo = ativo.id_ativo
            ordem.id_servico = servico.id_servico
            if criticidade:
                ordem.prioridade = str(criticidade)
        else:
            ordem = OrdemServico(
                titulo=agendamento_data.titulo,
                descricao=getattr(agendamento_data, "descricao", None) or agendamento_data.titulo,
                id_usuario=id_dono,
                id_ativo=ativo.id_ativo,
                id_servico=servico.id_servico,
                prioridade=str(criticidade) if criticidade else "Alta"
            )
            db.add(ordem)
            db.flush()
            agendamento.id_ordem_servico = ordem.id_ordem_servico

        data_ag = agendamento_data.data_agendamento
        if isinstance(data_ag, str):
            data_ag = datetime.fromisoformat(data_ag.replace("Z", "+00:00"))
        agendamento.data_agendamento = data_ag

        if getattr(agendamento_data, "status", None):
            agendamento.status = agendamento_data.status

        db.commit()
        db.refresh(agendamento)

        return {
            "message": "Agendamento atualizado com sucesso",
            "agendamento": {
                "id_agendamento": agendamento.id_agendamento,
                "data_agendamento": agendamento.data_agendamento.isoformat() if agendamento.data_agendamento else None,
                "status": agendamento.status,
                "id_ordem_servico": agendamento.id_ordem_servico
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar: {str(e)}")


@router.post("/teste")
def teste_criar():
    return {"message": "Rota de agendamentos funcionando"}
