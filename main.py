import asyncio
import json
import os  # Adicionado para ler as variáveis de ambiente do Kubernetes
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis.asyncio as redis # Versão assíncrona da lib
import logging

app = FastAPI(title="Livraria com Cache Redis")

# --- Configuração Dinâmica do Redis ---
# Se a aplicação rodar no Kubernetes, ela usará "redis-service" injetado pelo deployment.yaml.
# Se rodar localmente sem K8s, ela usará por padrão "localhost".
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# --- Modelo e Banco em Memória ---
class Livro(BaseModel):
    id: int
    titulo: str
    autor: str
    ano: int

db_livros: List[Livro] = [
    Livro(id=1, titulo="Dom Casmurro", autor="Machado de Assis", ano=1899),
    Livro(id=2, titulo="O Alquimista", autor="Paulo Coelho", ano=1988)
]

# --- Métodos Redis ---

async def salvar_livros_redis(livros: List[Livro]):
    """Salva a lista de livros no Redis com um tempo de expiração (TTL)."""
    # Convertemos a lista de modelos para uma string JSON
    livros_json = json.dumps([livro.model_dump() for livro in livros])
    # TTL de 60 segundos para teste
    await redis_client.set("livros", livros_json, ex=60)
    print("DEBUG: Dados salvos no Redis!")

async def deletar_livros_redis():
    """Remove a chave de livros do Redis para garantir consistência."""
    await redis_client.delete("livros")
    print("DEBUG: Cache do Redis limpo!")

# --- Endpoints ---
@app.get("/livros", response_model=List[Livro])
async def listar_livros():
    cache_livros = await redis_client.get("livros")
    
    if cache_livros:
        logging.info("Retornando dados do CACHE (Redis)") # <--- Alterado para logging
        return json.loads(cache_livros)

    logging.info("Cache vazio. Buscando no 'banco'...")   # <--- Alterado para logging
    await asyncio.sleep(2)
    
    await salvar_livros_redis(db_livros)
    return db_livros

@app.post("/livros", status_code=201)
async def criar_livro(novo_livro: Livro):
    """Adiciona um livro e limpa o cache para evitar dados obsoletos."""
    # Verifica se o ID já existe para evitar duplicidade
    if any(livro.id == novo_livro.id for livro in db_livros):
        raise HTTPException(status_code=400, detail="Livro com este ID já existe.")
        
    db_livros.append(novo_livro)
    # Sempre que houver alteração, deletamos o cache
    await deletar_livros_redis()
    return novo_livro
