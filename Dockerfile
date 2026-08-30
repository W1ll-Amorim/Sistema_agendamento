# 1. Usa uma imagem oficial e enxuta do Python
FROM python:3.10-slim

# 2. Define onde o código vai ficar dentro do container
WORKDIR /app

# 3. Copia os requerimentos primeiro (isso otimiza o tempo de build)
COPY requirements.txt .

# 4. Instala as dependências do sistema
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copia todo o resto do seu código para dentro do container
COPY . .

# 6. Libera a porta 8000 para acesso
EXPOSE 8000

# 7. Comando para rodar a aplicação (Ajustado para FastAPI)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# NOTA: Se você estiver usando Flask em vez de FastAPI/Uvicorn, troque a linha acima por:
# CMD ["flask", "run", "--host=0.0.0.0", "--port=8000"]