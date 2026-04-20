import asyncio
import json
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis.asyncio as redis # Versão assíncrona da lib

app = FastAPI(title="Livraria com Cache Redis")

# --- Configuração do Redis ---
# Em produção, essas infos viriam de variáveis de ambiente (.env)
REDIS_HOST = "localhost"
REDIS_PORT = 6379
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
    """Tenta buscar no Redis, se falhar, busca na lista e salva no cache."""
    # 1. Tenta buscar no Cache
    cache_livros = await redis_client.get("livros")
    
    if cache_livros:
        print("DEBUG: Retornando dados do CACHE (Redis)")
        return json.loads(cache_livros)

    # 2. Se não estiver no cache, simula busca lenta no 'banco'
    print("DEBUG: Cache vazio. Buscando no 'banco'...")
    await asyncio.sleep(2) # Simulação de lentidão
    
    # 3. Salva no Redis para a próxima consulta
    await salvar_livros_redis(db_livros)
    return db_livros

@app.post("/livros", status_code=201)
async def criar_livro(novo_livro: Livro):
    """Adiciona um livro e limpa o cache para evitar dados obsoletos."""
    db_livros.append(novo_livro)
    # Sempre que houver alteração, deletamos o cache
    await deletar_livros_redis()
    return novo_livro