FROM python:3.10-slim

WORKDIR /app

# Copia os arquivos de requisitos e instala as dependências
RUN pip install --no-cache-dir fastapi uvicorn redis

# Copia o seu arquivo main.py para dentro do contêiner
COPY main.py .

# Comando para iniciar a API apontando para a porta 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]