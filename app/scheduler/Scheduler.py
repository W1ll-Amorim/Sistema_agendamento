from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from app.core.database import SessionLocal, DATABASE_URL
from app.models.models import OrdemServico


# ---------------------------------------------------------------------------
# 1. Job store persistente (SQLAlchemy)
#    Os jobs ficam salvos no banco. Se o servidor reiniciar, os agendamentos
#    nao sao perdidos.
# ---------------------------------------------------------------------------
jobstores = {
    "default": SQLAlchemyJobStore(url=DATABASE_URL)
}

# BackgroundScheduler roda em thread separada (nao trava o FastAPI)
scheduler = BackgroundScheduler(jobstores=jobstores)


# ---------------------------------------------------------------------------
# 2. Ligar / desligar o scheduler (chamados no startup/shutdown do FastAPI)
# ---------------------------------------------------------------------------
def start_scheduler():
    """Inicia o APScheduler se ainda nao estiver rodando."""
    if not scheduler.running:
        scheduler.start()
        print("APScheduler iniciado.")


def stop_scheduler():
    """Encerra o APScheduler de forma limpa (no shutdown da aplicacao)."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("APScheduler finalizado.")


# ---------------------------------------------------------------------------
# 3. Job executado na data/hora agendada
# ---------------------------------------------------------------------------
def executar_ordem(id_ordem_servico: str):
    """
    Callback disparado pelo APScheduler quando chega a data_execucao.
    Abre uma sessao propria do banco (a thread do scheduler nao compartilha
    a sessao do request HTTP) e marca a ordem como 'Em execucao'.
    """
    db = SessionLocal()
    try:
        ordem = (
            db.query(OrdemServico)
            .filter_by(id_ordem_servico=id_ordem_servico)
            .first()
        )
        if ordem:
            ordem.status = "Em execução"
            db.commit()
            print(f"Ordem '{ordem.titulo}' (id={id_ordem_servico}) iniciada!")
        else:
            print(f"Ordem {id_ordem_servico} nao encontrada ao executar job.")
    except Exception as e:
        db.rollback()
        print(f"Erro ao executar ordem {id_ordem_servico}: {e}")
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 4. Agendar uma ordem para uma data futura
# ---------------------------------------------------------------------------
def agendar_ordem(data_execucao: datetime, id_ordem_servico: str):
    """
    Registra (ou substitui) um job unico com trigger 'date'.

    - job_id usa o prefixo 'ordem:' para nao colidir com outros jobs.
    - replace_existing=True: se ja existir job para essa ordem, atualiza.
    - misfire_grace_time=3600: se o servidor estiver offline na hora exata,
      ainda tenta executar ate 1 hora depois de voltar.
    """
    if data_execucao is None:
        print("agendar_ordem: data_execucao e None, job nao criado.")
        return None

    # Garante datetime naive/aware consistente com o scheduler
    if isinstance(data_execucao, str):
        data_execucao = datetime.fromisoformat(data_execucao.replace("Z", "+00:00"))

    job_id = f"ordem:{id_ordem_servico}"

    try:
        # Se o scheduler ainda nao foi startado, starta (defesa)
        if not scheduler.running:
            start_scheduler()

        scheduler.add_job(
            executar_ordem,
            trigger="date",
            run_date=data_execucao,
            args=[str(id_ordem_servico)],
            id=job_id,
            replace_existing=True,
            misfire_grace_time=3600,
        )
        print(f"Job {job_id} agendado para {data_execucao}")
        return job_id
    except Exception as e:
        print(f"Erro ao agendar job {job_id}: {e}")
        return None


# ---------------------------------------------------------------------------
# 5. Utilitarios de gestao de jobs
# ---------------------------------------------------------------------------
def listar_jobs():
    """Retorna a lista de jobs ainda pendentes no scheduler."""
    return scheduler.get_jobs()


def cancelar_job(job_id: str):
    """Remove um job pelo id (ex.: 'ordem:<uuid>')."""
    if not job_id:
        return
    try:
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
            print(f"Job {job_id} cancelado.")
        else:
            print(f"Job {job_id} nao encontrado para cancelar.")
    except Exception as e:
        print(f"Erro ao cancelar job {job_id}: {e}")


def cancelar_job_por_ordem(id_ordem_servico: str):
    """Atalho: cancela o job associado a uma ordem de servico."""
    cancelar_job(f"ordem:{id_ordem_servico}")