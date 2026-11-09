FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependências do PostgreSQL e criação do usuário
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 appuser

# Instalação das dependências Python
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Cópia dos arquivos da aplicação
COPY --chown=appuser:appuser . .

# Cópia e preparação do entrypoint
COPY --chmod=755 scripts/entrypoint.sh /usr/local/bin/entrypoint.sh

# Padronização de quebras de linha e permissões
RUN sed -i 's/\r$//' /usr/local/bin/entrypoint.sh \
    && chmod 755 /usr/local/bin/entrypoint.sh

# Execução sem privilégios de root
USER appuser

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]