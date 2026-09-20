from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from app.core.database import SessionLocal
from app.models.models import Agendamento, OrdemServico

scheduler = BackgroundScheduler()

def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        print("APScheduler iniciado.")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        print("APScheduler finalizado.")

def executar_ordem(id_ordem_servico: str):
    db = SessionLocal()
    try:
        ordem = db.query(OrdemServico).filter_by(id_ordem_servico=id_ordem_servico).first()
        if ordem:
            ordem.status = "Em execução"
            db.commit()
            print(f"Ordem {ordem.titulo} iniciada!")
    finally:
        db.close()

def agendar_ordem(data_execucao: datetime, id_ordem_servico: str):
    job_id = str(id_ordem_servico)
    scheduler.add_job(
        executar_ordem,
        trigger="date",
        run_date=data_execucao,
        args=[id_ordem_servico],
        id=job_id,
        replace_existing=True
    )
    return job_id

def listar_jobs():
    return scheduler.get_jobs()

def cancelar_job(job_id: str):
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        print(f"Job {job_id} cancelado.")