# Imagem base leve com Python
FROM python:3.10-slim

# Definir diretório de trabalho dentro do container
WORKDIR /app

# Instalar dependências do sistema (útil para grpc e cryptography)
RUN apt-get update && apt-get install -y \
    build-essential libssl-dev libffi-dev python3-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependências e instalar
COPY requirements_venv.txt .
RUN pip install --no-cache-dir -r requirements_venv.txt

# Copiar o restante do código
COPY . .

# Expor porta FastAPI
EXPOSE 8000

ENV PYTHONPATH="/app/backend"

# Comando para iniciar a API
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
