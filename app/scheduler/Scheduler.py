from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from app.core.database import SessionLocal, DATABASE_URL
from app.models.models import OrdemServico


jobstores = {
    "default": SQLAlchemyJobStore(
        url=DATABASE_URL
    )
}

scheduler = BackgroundScheduler(
    jobstores=jobstores
)


def start_scheduler():

    if not scheduler.running:
        scheduler.start()


def executar_ordem(id_ordem_servico: str):

    db = SessionLocal()

    try:

        ordem = (
            db.query(OrdemServico)
            .filter_by(
                id_ordem_servico=id_ordem_servico
            )
            .first()
        )

        if ordem:

            ordem.status = "Em execução"

            db.commit()

            print(
                f"Ordem {ordem.titulo} iniciada!"
            )

    finally:

        db.close()


def agendar_ordem(
    data_execucao: datetime,
    id_ordem_servico: str
):

    job_id = f"ordem:{id_ordem_servico}"

    scheduler.add_job(
        executar_ordem,
        trigger="date",
        run_date=data_execucao,
        args=[id_ordem_servico],
        id=job_id,
        replace_existing=True,
        misfire_grace_time=3600
    )

    return job_id


def listar_jobs():

    return scheduler.get_jobs()


def cancelar_job(job_id: str):

    if scheduler.get_job(job_id):

        scheduler.remove_job(job_id)