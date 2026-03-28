from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from app.core.database import SessionLocal
from app.models.models import Agendamento, OrdemServico

scheduler = BackgroundScheduler()
scheduler.start()

def executar_odrdem(id_ordem_servico: str):

    db = SessionLocal()

    try:
        ordem = db.query(OrdemServico).filter_by(id_ordem_servico).first()

        if ordem:
            ordem.status = "Em execução"
            db.commit()

            print(f"Ordem {ordem.titulo} iniciada!")

    finally:
        db.close()


def agendar_ordem(data_execucao: datetime, id_ordem_servico: str):

    scheduler.add_job(
        executar_odrdem,
        trigger="date",
        run_date=data_execucao,
        args=[id_ordem_servico]
    )

def listar_jobs():
    return scheduler.get_jobs()


def cancelar_job (job_id: str):
    scheduler.remove_job(job_id)

