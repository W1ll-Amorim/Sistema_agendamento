from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import uuid
import enum
from sqlalchemy import Enum

class prioridade (enum.Enum):
    baixo = "Baixo"
    medio = "Médio"
    alto  = "Alto"

class UsuarioEmpresa(Base):
    _tablename_ = "usuario_empresa"

    id_usuario = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nome = Column(String, nullable=False)
    email = Column(String, unique=True)
    senha_hash = Column(String, nullable= False)
    telefone = Column(String)
    endereco = Column (String)
    # Um usuário pode ter vários agendamentos
    agendamentos = relationship("Agendamento", back_populates="usuario")

class Agendamento(Base):
    __tablename__ = "agendamento"

    id_agendamento = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    data_agendamento = Column(DateTime, default = DateTime.datetime.utcnow )
    status = Column(String, default= "Agendado")
    id_ordem_servico = Column(String, ForeignKey("ordem_servico.id_ordem_servico"), nullable=False)
    id_usuario = Column(String, ForeignKey("usuario_empresa.id_usuario"), nullable=False)
    # Cada agendamento pertence a UM usuário
    usuario = relationship("UsuarioEmpresa", back_populates="agendamentos")
    
    # Cada agendamento está ligado a UMA ordem de serviço
    ordem_servico = relationship("OrdemServico", back_populates="agendamentos")
    
class OrdemServico(Base):
    __tablename__ = "orden_servico"


    # Uma ordem de serviço pode estar em vários agendamentos (ou um só)
    agendamentos = relationship("Agendamento", back_populates="ordem_servico")
class TipoServico(Base):
    __tablename__ = "tipo_servico"
    id_servico = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nome = Column(String, nullable=False)
    descricao = Column(String)
    nivel_prioridade = Column(Enum(prioridade), default=prioridade.baixo,# Valor padrão caso não seja enviado nada
    nullable=False
    )


class Ativo(Base):
    __tablename__ = "ativo"




class Historico(Base):
    __tablename__ = "historico"

