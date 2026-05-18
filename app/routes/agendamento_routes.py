from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.database import get_db
from app.core.security import verificar_token
from datetime import datetime
from app.models.models import Agendamento, OrdemServico, Ativo, TipoServico
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
    try:
        # Primeiro, verificar se o serviço já existe, senão criar
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

        # Segundo, verificar se o ativo já existe, senão criar
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

        # Terceiro, criar a ordem de serviço
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

        # Quarto, criar o agendamento
        novo_agendamento = Agendamento(
            id_ordem_servico=nova_ordem.id_ordem_servico,
            id_usuario=agendamento_data.id_usuario,
            data_agendamento=agendamento_data.data_agendamento,
            status=agendamento_data.status
        )

        db.add(novo_agendamento)
        db.commit()
        db.refresh(novo_agendamento)

        # Aciona o disparador de tarefas automáticas vindo do GitHub
        agendar_ordem(agendamento_data.data_agendamento, nova_ordem.id_ordem_servico)

        return {
            "message": "Agendamento criado com sucesso",
            "agendamento": {
                "id_agendamento": novo_agendamento.id_agendamento,
                "id_ordem_servico": nova_ordem.id_ordem_servico,
                "titulo": agendamento_data.titulo,
                "data_agendamento": agendamento_data.data_agendamento.isoformat()
            }
        }
    except Exception as e:
        db.rollback()
        return {"error": f"Erro ao criar agendamento: {str(e)}"}

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
        return {"error": str(e)}

@router.get("/")
def listar_agendamentos(id_usuario: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        agendamentos = db.query(Agendamento).filter(
            Agendamento.id_usuario == id_usuario
        ).all()

        resultado = []
        for agendamento in agendamentos:
            ordem = db.query(OrdemServico).filter(
                OrdemServico.id_ordem_servico == agendamento.id_ordem_servico
            ).first()
            
            if ordem:
                ativo = db.query(Ativo).filter(Ativo.id_ativo == ordem.id_ativo).first()
                servico = db.query(TipoServico).filter(TipoServico.id_servico == ordem.id_servico).first()
                
                resultado.append({
                    "id_agendamento": agendamento.id_agendamento,
                    "titulo": ordem.titulo or "Sem título",
                    "descricao": ordem.descricao or "",
                    "nome_ativo": ativo.nome if ativo else "Ativo não encontrado",
                    "tipo_ativo": ativo.tipo if ativo else "",
                    "nome_servico": servico.nome if servico else "Serviço não encontrado",
                    "data_agendamento": agendamento.data_agendamento.isoformat(),
                    "id_ordem_servico": agendamento.id_ordem_servico,
                    "status": agendamento.status or "Tarefas",
                    "criticidade": ordem.prioridade if ordem and getattr(ordem, 'prioridade', None) else None
                })

        return {"agendamentos": resultado}
    except Exception as e:
        return {"error": f"Erro ao listar agendamentos: {str(e)}"}

@router.delete("/{id_agendamento}")
def deletar_agendamento(id_agendamento: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        agendamento = db.query(Agendamento).filter(
            Agendamento.id_agendamento == id_agendamento
        ).first()

        if not agendamento:
            return {"error": "Agendamento não encontrado"}

        db.delete(agendamento)
        db.commit()

        return {"message": "Agendamento deletado com sucesso"}
    except Exception as e:
        db.rollback()
        return {"error": f"Erro ao deletar agendamento: {str(e)}"}

@router.put("/{id_agendamento}/status")
def atualizar_status_agendamento(id_agendamento: str, novo_status: str = Query(...), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        agendamento = db.query(Agendamento).filter(
            Agendamento.id_agendamento == id_agendamento
        ).first()

        if not agendamento:
            return {"error": "Agendamento não encontrado"}

        agendamento.status = novo_status
        db.commit()
        db.refresh(agendamento)

        return {"message": "Status updated com sucesso", "novo_status": novo_status}
    except Exception as e:
        db.rollback()
        return {"error": f"Erro ao atualizar status: {str(e)}"}


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
            return {"error": "Agendamento não encontrado"}

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
        return {"error": f"Erro ao atualizar agendamento: {str(e)}"}