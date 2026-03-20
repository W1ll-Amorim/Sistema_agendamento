from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler

scheduler.start()

def executar_tarefa(titulo):

    print("Executando tarefa:", titulo)