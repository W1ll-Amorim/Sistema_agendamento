from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.database import get_db
from app.core.security import verificar_token
from datetime import datetime
from typing import Optional
from app.models.models import Agendamento, OrdemServico, Ativo, TipoServico, UsuarioEmpresa
from app.schemas.agendamento_schema import AgendamentoCreate, AgendamentoResponse
from app.scheduler.Scheduler import agendar_ordem # Reativado do GitHub

# Dependência para verificar autenticação
def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token de autenticação não fornecido")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Formato de token inválido")
    
    token = authorization.replace("Bearer ", "")
    payload = verificar_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    
    return payload


router = APIRouter(prefix="", tags=["Agendamentos"])

@router.post("/teste")
def teste_criar():
    return {"message": "Rota funcionando"}

@router.post("/")
def criar_agendamento_completo(
    agendamento_data: AgendamentoCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Cria serviço/ativo/ordem/agendamento em uma única transação."""
    try:
        id_usuario = str(agendamento_data.id_usuario).strip() if agendamento_data.id_usuario is not None else ""
        # Resolve id a partir do token se o cliente mandou valor inválido
        if not id_usuario or id_usuario in ("None", "nan", "NaN"):
            email = current_user.get("sub") if isinstance(current_user, dict) else None
            if email:
                u = db.query(UsuarioEmpresa).filter(UsuarioEmpresa.email == email).first()
                if u:
                    id_usuario = u.id_usuario
        if not id_usuario:
            raise HTTPException(status_code=400, detail="id_usuario inválido ou ausente")

        usuario_existe = db.query(UsuarioEmpresa).filter(
            UsuarioEmpresa.id_usuario == id_usuario
        ).first()
        if not usuario_existe:
            raise HTTPException(status_code=400, detail=f"Usuário não encontrado: {id_usuario}")

        servico = db.query(TipoServico).filter(
            TipoServico.nome == agendamento_data.nome_servico
        ).first()
        if not servico:
            servico = TipoServico(
                nome=agendamento_data.nome_servico,
                descricao=agendamento_data.descricao_servico
            )
            db.add(servico)
            db.flush()

        ativo = db.query(Ativo).filter(
            Ativo.nome == agendamento_data.nome_ativo,
            Ativo.id_usuario == id_usuario
        ).first()
        if not ativo:
            ativo = Ativo(
                nome=agendamento_data.nome_ativo,
                tipo=agendamento_data.tipo_ativo,
                id_usuario=id_usuario
            )
            db.add(ativo)
            db.flush()

        nova_ordem = OrdemServico(
            titulo=agendamento_data.titulo,
            descricao=agendamento_data.descricao,
            id_usuario=id_usuario,
            id_ativo=ativo.id_ativo,
            id_servico=servico.id_servico,
            status=agendamento_data.status or "Pendente",
            prioridade=getattr(agendamento_data, 'criticidade', None)
        )
        db.add(nova_ordem)
        db.flush()

        novo_agendamento = Agendamento(
            id_ordem_servico=nova_ordem.id_ordem_servico,
            id_usuario=id_usuario,
            data_agendamento=agendamento_data.data_agendamento,
            status=agendamento_data.status or "Pendente"
        )
        db.add(novo_agendamento)
        db.commit()
        db.refresh(novo_agendamento)

        try:
            agendar_ordem(agendamento_data.data_agendamento, nova_ordem.id_ordem_servico)
        except Exception as sched_err:
            print(f"Aviso scheduler: {sched_err}")

        return {
            "message": "Agendamento criado com sucesso",
            "agendamento": {
                "id_agendamento": novo_agendamento.id_agendamento,
                "id_ordem_servico": nova_ordem.id_ordem_servico,
                "titulo": agendamento_data.titulo,
                "data_agendamento": agendamento_data.data_agendamento.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao criar agendamento: {str(e)}")

@router.post("/simples")
def criar_agendamento_simples(
    titulo: str,
    id_usuario: str,
    data_agendamento: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        from datetime import datetime
        data = datetime.fromisoformat(data_agendamento.replace('Z', '+00:00'))
        
        novo_agendamento = Agendamento(
            id_ordem_servico="teste-ordem",
            id_usuario=id_usuario,
            data_agendamento=data
        )

        db.add(novo_agendamento)
        db.commit()
        db.refresh(novo_agendamento)

        return {"message": "Agendamento simples criado", "id": novo_agendamento.id_agendamento}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
def listar_agendamentos(
    id_usuario: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Lista agendamentos conforme perfil.
    - ADMIN / TECNICO: todas as tarefas (a menos que id_usuario seja passado).
    - COMUM: apenas as próprias.
    """
    try:
        from app.models.models import UsuarioEmpresa, TipoUsuario

        def norm_tipo(u):
            if u is None:
                return "COMUM"
            t = getattr(u, "tipo", None)
            if t is None:
                return "COMUM"
            if isinstance(t, TipoUsuario):
                return t.name  # COMUM, TECNICO, ADMIN
            s = str(t).strip()
            # "TipoUsuario.ADMIN" / "admin" / "ADMIN"
            if "." in s:
                s = s.split(".")[-1]
            s = s.upper()
            if s in ("COMUM", "TECNICO", "ADMIN"):
                return s
            return "COMUM"

        email = None
        if isinstance(current_user, dict):
            email = current_user.get("sub")

        usuario_logado = None
        if email:
            usuario_logado = (
                db.query(UsuarioEmpresa)
                .filter(UsuarioEmpresa.email == email)
                .first()
            )

        if usuario_logado is None:
            raise HTTPException(status_code=401, detail="Usuário do token não encontrado")

        tipo_nome = norm_tipo(usuario_logado)

        query = db.query(Agendamento)

        # Filtro explícito por dono (opcional)
        if id_usuario:
            query = query.filter(Agendamento.id_usuario == str(id_usuario))
        elif tipo_nome not in ("ADMIN", "TECNICO"):
            # COMUM (ou desconhecido): só as próprias
            query = query.filter(Agendamento.id_usuario == usuario_logado.id_usuario)
        # ADMIN / TECNICO sem id_usuario → todas

        try:
            agendamentos = query.order_by(Agendamento.data_agendamento.desc()).all()
        except Exception:
            agendamentos = query.all()

        resultado = []
        for agendamento in agendamentos:
            ordem = None
            ativo = None
            servico = None
            try:
                if agendamento.id_ordem_servico:
                    ordem = (
                        db.query(OrdemServico)
                        .filter(OrdemServico.id_ordem_servico == agendamento.id_ordem_servico)
                        .first()
                    )
                if ordem:
                    if ordem.id_ativo:
                        ativo = db.query(Ativo).filter(Ativo.id_ativo == ordem.id_ativo).first()
                    if ordem.id_servico:
                        servico = (
                            db.query(TipoServico)
                            .filter(TipoServico.id_servico == ordem.id_servico)
                            .first()
                        )
            except Exception as join_err:
                print(f"Aviso join agendamento {agendamento.id_agendamento}: {join_err}")

            data_iso = None
            if agendamento.data_agendamento is not None:
                try:
                    data_iso = agendamento.data_agendamento.isoformat()
                except Exception:
                    data_iso = str(agendamento.data_agendamento)

            criticidade = None
            if ordem is not None:
                criticidade = getattr(ordem, "prioridade", None)

            resultado.append({
                "id_agendamento": agendamento.id_agendamento,
                "id_usuario": agendamento.id_usuario,
                "titulo": (ordem.titulo if ordem else None) or "Sem título",
                "descricao": (ordem.descricao if ordem else None) or "",
                "nome_ativo": (ativo.nome if ativo else None) or "Geral",
                "tipo_ativo": (ativo.tipo if ativo else None) or "",
                "nome_servico": (servico.nome if servico else None) or "",
                "descricao_servico": (servico.descricao if servico else None) or "",
                "data_agendamento": data_iso,
                "id_ordem_servico": agendamento.id_ordem_servico,
                "status": agendamento.status
                    or (ordem.status if ordem else None)
                    or "Pendente",
                "criticidade": criticidade or "Alta",
            })

        return {"agendamentos": resultado}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Erro ao listar agendamentos: {str(e)}")

@router.delete("/{id_agendamento}")
def deletar_agendamento(id_agendamento: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        agendamento = db.query(Agendamento).filter(
            Agendamento.id_agendamento == id_agendamento
        ).first()

        if not agendamento:
            raise HTTPException(status_code=404, detail="Agendamento não encontrado")

        db.delete(agendamento)
        db.commit()

        return {"message": "Agendamento deletado com sucesso"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao deletar agendamento: {str(e)}")

@router.put("/{id_agendamento}/status")
def atualizar_status_agendamento(id_agendamento: str, novo_status: str = Query(...), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        agendamento = db.query(Agendamento).filter(
            Agendamento.id_agendamento == id_agendamento
        ).first()

        if not agendamento:
            raise HTTPException(status_code=404, detail="Agendamento não encontrado")

        agendamento.status = novo_status
        db.commit()
        db.refresh(agendamento)

        return {"message": "Status updated com sucesso", "novo_status": novo_status}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao atualizar status: {str(e)}")


@router.put("/{id_agendamento}")
def atualizar_agendamento(
    id_agendamento: str,
    agendamento_data: AgendamentoCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        agendamento = db.query(Agendamento).filter(
            Agendamento.id_agendamento == id_agendamento
        ).first()

        if not agendamento:
            raise HTTPException(status_code=404, detail="Agendamento não encontrado")

        servico = db.query(TipoServico).filter(
            TipoServico.nome == agendamento_data.nome_servico
        ).first()

        if not servico:
            servico = TipoServico(
                nome=agendamento_data.nome_servico,
                descricao=agendamento_data.descricao_servico
            )
            db.add(servico)
            db.commit()
            db.refresh(servico)

        ativo = db.query(Ativo).filter(
            Ativo.nome == agendamento_data.nome_ativo,
            Ativo.id_usuario == agendamento_data.id_usuario
        ).first()

        if not ativo:
            ativo = Ativo(
                nome=agendamento_data.nome_ativo,
                tipo=agendamento_data.tipo_ativo,
                id_usuario=agendamento_data.id_usuario
            )
            db.add(ativo)
            db.commit()
            db.refresh(ativo)

        ordem = db.query(OrdemServico).filter(
            OrdemServico.id_ordem_servico == agendamento.id_ordem_servico
        ).first()

        if ordem:
            ordem.titulo = agendamento_data.titulo
            ordem.descricao = agendamento_data.descricao
            ordem.id_ativo = ativo.id_ativo
            ordem.id_servico = servico.id_servico
            ordem.prioridade = getattr(agendamento_data, 'criticidade', ordem.prioridade)
            db.commit()
            db.refresh(ordem)
        else:
            nova_ordem = OrdemServico(
                titulo=agendamento_data.titulo,
                descricao=agendamento_data.descricao,
                id_usuario=agendamento_data.id_usuario,
                id_ativo=ativo.id_ativo,
                id_servico=servico.id_servico,
                prioridade=getattr(agendamento_data, 'criticidade', None)
            )
            db.add(nova_ordem)
            db.commit()
            db.refresh(nova_ordem)
            agendamento.id_ordem_servico = nova_ordem.id_ordem_servico

        agendamento.data_agendamento = agendamento_data.data_agendamento
        if agendamento_data.status:
            agendamento.status = agendamento_data.status

        db.commit()
        db.refresh(agendamento)

        return {
            "message": "Agendamento atualizado com sucesso",
            "agendamento": {
                "id_agendamento": agendamento.id_agendamento,
                "data_agendamento": agendamento.data_agendamento.isoformat(),
                "status": agendamento.status,
                "id_ordem_servico": agendamento.id_ordem_servico
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao atualizar agendamento: {str(e)}")