from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
import uuid
import enum
from datetime import datetime
from database import Base #o Base vem do seu arquivo de config database.db

class Prioridade(enum.Enum):
    baixo = "Baixo"
    medio = "Médio"
    alto  = "Alto"

class UsuarioEmpresa(Base):
    __tablename__ = "usuario_empresa"

    id_usuario = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nome = Column(String, nullable=False)
    email = Column(String, unique=True)
    senha_hash = Column(String, nullable=False)
    telefone = Column(String)
    endereco = Column(String)

    # Relacionamentos
    agendamentos = relationship("Agendamento", back_populates="usuario")
    ordens_servico = relationship("OrdemServico", back_populates="usuario")
    ativos = relationship("Ativo", back_populates="usuario")

class Ativo(Base):
    __tablename__ = "ativo"

    id_ativo = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nome = Column(String, nullable=False)
    tipo = Column(String)
    marca_modelo = Column(String)
    numero_serie = Column(String, unique=True)
    id_usuario = Column(String, ForeignKey("usuario_empresa.id_usuario"), nullable=False)

    usuario = relationship("UsuarioEmpresa", back_populates="ativos")
    ordens_servico = relationship("OrdemServico", back_populates="ativo")

class TipoServico(Base):
    __tablename__ = "tipo_servico"

    id_servico = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nome = Column(String, nullable=False)
    descricao = Column(String)
    nivel_prioridade = Column(Enum(Prioridade), default=Prioridade.baixo, nullable=False)

    ordens_servico = relationship("OrdemServico", back_populates="tipo_servico")

class OrdemServico(Base):
    __tablename__ = "ordem_servico"

    id_ordem_servico = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    titulo = Column(String)
    descricao = Column(String)
    data_criacao = Column(DateTime, default=datetime.utcnow)
    status = Column(String)
    
    # Chaves Estrangeiras (Onde os dados se conectam)
    id_usuario = Column(String, ForeignKey("usuario_empresa.id_usuario"), nullable=False)
    id_ativo = Column(String, ForeignKey("ativo.id_ativo"), nullable=False)
    id_servico = Column(String, ForeignKey("tipo_servico.id_servico"), nullable=False)

    # Relacionamentos
    usuario = relationship("UsuarioEmpresa", back_populates="ordens_servico")
    ativo = relationship("Ativo", back_populates="ordens_servico")
    tipo_servico = relationship("TipoServico", back_populates="ordens_servico")
    agendamentos = relationship("Agendamento", back_populates="ordem_servico")
    historicos = relationship("Historico", back_populates="ordem_servico")

class Agendamento(Base):
    __tablename__ = "agendamento"

    job_id = Column(String)
    id_agendamento = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    data_agendamento = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="Agendado")
    
    id_ordem_servico = Column(String, ForeignKey("ordem_servico.id_ordem_servico"), nullable=False)
    id_usuario = Column(String, ForeignKey("usuario_empresa.id_usuario"), nullable=False)

    usuario = relationship("UsuarioEmpresa", back_populates="agendamentos")
    ordem_servico = relationship("OrdemServico", back_populates="agendamentos")

class Historico(Base):
    __tablename__ = "historico"

    id_historico = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    data_registro = Column(DateTime, default=datetime.utcnow)
    acao = Column(String)
    observacao = Column(String)
    condicionamento = Column(String)
    
    id_ordem_servico = Column(String, ForeignKey("ordem_servico.id_ordem_servico"), nullable=False)
    id_usuario = Column(String, ForeignKey("usuario_empresa.id_usuario"), nullable=False)

    ordem_servico = relationship("OrdemServico", back_populates="historicos")