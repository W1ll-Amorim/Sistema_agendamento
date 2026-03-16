from sqlalchemy import column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import uuid

class User(Base):
    _tablename_ = "users"

    id = column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nome = column(String)
    email = column(String)
    senha = column(String)

class Tasks(Base):
    _tablename_ = "tasks"

    id
    user_id = column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    titulo = column(String)
    descricao = column(String)
    data_hora = column(DateTime)
    status = column(String)