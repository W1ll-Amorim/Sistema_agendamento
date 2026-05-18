from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AgendamentoCreate(BaseModel):
    titulo: str
    descricao: str
    nome_ativo: str
    tipo_ativo: str
    nome_servico: str
    descricao_servico: str
    data_agendamento: datetime
    id_usuario: str
    status: Optional[str] = "Tarefas"
    criticidade: Optional[str] = None

class AgendamentoResponse(BaseModel):
    id_agendamento: str
    job_id: str
    data_agendamento: datetime
    status: str
    id_ordem_servico: str
    id_usuario: str

    class Config:
        from_attributes = True