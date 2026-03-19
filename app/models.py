from sqlalchemy import column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import uuid

class User(Base):
    _tablename_ = "usuario_empresa"

    id_usuario = column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nome = column(String, nullable=False)
    email = column(String, unique=True)
    senha_hash = column(String, nullable= False)
    telefone = column(String)
    endereco = column (String)

class Tasks(Base):
    _tablename_ = "agendamento"

    id_agendamento = column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    data_agendamento = column(DateTime, default = DateTime.datetime.utcnow )
    status = column(String, default= "Agendado")
    id_ordem_servico = column(String, ForeignKey("ordem_servico.id_ordem_servico"), nullable=False)
    id_usuario = column(String, ForeignKey("usuario_empresa.id_usuario"), nullable=False)
    