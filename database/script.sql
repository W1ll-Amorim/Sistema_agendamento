PRAGMA foreign_keys = ON;

CREATE TABLE usuario_empresa (
    id_usuario TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    email TEXT,
    telefone TEXT,
    endereco TEXT
);

CREATE TABLE tipo_servico (
    id_servico TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    descricao TEXT,
    nivel_prioridade TEXT
);

CREATE TABLE ativo (
    id_ativo TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    tipo TEXT,
    marca_modelo TEXT,
    numero_serie TEXT,
    id_usuario TEXT NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuario_empresa(id_usuario)
);

CREATE TABLE ordem_servico (
    id_ordem_servico TEXT PRIMARY KEY,
    titulo TEXT,
    descricao TEXT,
    data_criacao DATETIME,
    status TEXT,
    id_usuario TEXT NOT NULL,
    id_ativo TEXT NOT NULL,
    id_servico TEXT NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuario_empresa(id_usuario),
    FOREIGN KEY (id_ativo) REFERENCES ativo(id_ativo),
    FOREIGN KEY (id_servico) REFERENCES tipo_servico(id_servico)
);

CREATE TABLE agendamento (
    id_agendamento TEXT PRIMARY KEY,
    data_agendamento DATETIME,
    status TEXT,
    id_ordem_servico TEXT NOT NULL,
    id_usuario TEXT NOT NULL,
    FOREIGN KEY (id_ordem_servico) REFERENCES ordem_servico(id_ordem_servico),
    FOREIGN KEY (id_usuario) REFERENCES usuario_empresa(id_usuario)
);

CREATE TABLE historico (
    id_historico TEXT PRIMARY KEY,
    data_registro DATETIME,
    acao TEXT,
    observacao TEXT,
    condicionamento TEXT,
    id_ordem_servico TEXT NOT NULL,
    id_usuario TEXT NOT NULL,
    FOREIGN KEY (id_ordem_servico) REFERENCES ordem_servico(id_ordem_servico),
    FOREIGN KEY (id_usuario) REFERENCES usuario_empresa(id_usuario)
);