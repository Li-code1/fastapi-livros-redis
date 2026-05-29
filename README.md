# 📚 API Livraria 3.0: Performance com Redis Cache & Orquestração Kubernetes

Este projeto é uma evolução da API de Livros em FastAPI. O objetivo principal foi implementar uma camada de **Cache** utilizando o **Redis** para otimizar o tempo de resposta da listagem de livros e, em seguida, **orquestrar a aplicação completa em contêineres utilizando Kubernetes**, garantindo alta disponibilidade com réplicas e isolamento de rede.

## 🛠️ Tecnologias e Conceitos

* **FastAPI**: Desenvolvimento de endpoints assíncronos.
* **Redis**: Armazenamento de dados em memória para cache rápido.
* **Cache-Aside Pattern & Invalidação**: Lógica para leitura e limpeza inteligente do cache.
* **Docker**: Conteinerização da aplicação FastAPI utilizando imagens leves (`python:3.10-slim`).
* **Kubernetes (K8s)**: Orquestração dos microsserviços.
* **Kind (Kubernetes in Docker)**: Ferramenta para execução do cluster local diretamente no **GitHub Codespaces**.

---

## 🏗️ Arquitetura no Kubernetes

A aplicação dentro do cluster foi dividida de forma resiliente e escalável:

* **FastAPI Deployment**: Configurado com **2 Réplicas (Pods)** rodando em paralelo para garantir que a API nunca fique fora do ar.
* **FastAPI Service (`ClusterIP`)**: Um ponto de entrada interno que distribui a carga entre as réplicas na porta `80`.
* **Redis Deployment & Service (`ClusterIP`)**: Uma instância isolada do Redis protegida na rede interna do cluster através do DNS estável `redis-service`.

---

## ⚙️ Configuração do Ambiente e Execução (GitHub Codespaces)

Como o projeto está preparado para rodar no ambiente em nuvem do **Codespaces**, siga os passos abaixo no terminal integrado:

### 1. Inicializar o Cluster Kubernetes (Kind)
O Codespaces já vem com o Docker instalado. Execute os comandos abaixo para instalar o **Kind** e provisionar o cluster:

```bash
# Baixar e configurar o binário do Kind
curl -Lo ./kind [https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64](https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64)
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# Criar o cluster Kubernetes
kind create cluster --name meu-cluster

```

### 2. Construir e Carregar a Imagem Docker da API

Gere a imagem do seu código fonte e envie-a para dentro do ecossistema de nós do Kind:

```bash
# Build da imagem local
docker build -t sua-imagem-docker .

# Enviar a imagem para dentro do cluster
kind load docker-image sua-imagem-docker --name meu-cluster

```

### 3. Aplicar os Manifestos no Kubernetes

Aplique as configurações na ordem correta (o banco de cache precisa subir primeiro para que a API consiga se conectar):

```bash
# 1. Subir a infraestrutura do Redis Cache
kubectl apply -f redis-manifest.yaml

# 2. Subir as duas réplicas do Backend FastAPI
kubectl apply -f deployment.yaml

# 3. Criar a rede de comunicação interna da API
kubectl apply -f service.yaml

```

Para verificar se todos os 3 Pods estão ativos e saudáveis, rode:

```bash
kubectl get pods

```

---

## 🧪 Guia de Testes via Postman / Navegador

Como os serviços no Kubernetes foram configurados como `ClusterIP` (protegidos contra acessos externos diretamente), precisamos abrir um túnel seguro para testar na nossa máquina:

```bash
kubectl port-forward service/fastapi-service 8080:80

```

> **Nota no Codespaces:** Assim que executar o comando acima, o GitHub exibirá um pop-up no canto inferior direito. Clique em **"Open in Browser"** para abrir a página ou utilize a URL gerada no Postman alterando a porta padrão para **8080**.

### 1. Listar Livros - Primeira Chamada (Cache Miss)

* **Método:** `GET`
* **URL:** `http://localhost:8080/livros`
* **O que observar:** A resposta vai demorar cerca de 2 segundos (simulando a busca lenta no banco). O log interno de um dos Pods registrará `DEBUG: Dados salvos no Redis!`.

### 2. Listar Livros - Chamadas Seguintes (Cache Hit)

* **Ação:** Clique em **Send** novamente para o mesmo endpoint.
* **O que observar:** O retorno será **instantâneo** (< 50ms). O tráfego agora está sendo respondido de forma ultra rápida pelo Pod do Redis de dentro do cluster.

### 3. Cadastrar Livro (Invalidação Automática de Cache)

* **Método:** `POST`
* **URL:** `http://localhost:8080/livros`
* **Body (JSON):**

```json
{
    "id": 5,
    "titulo": "A Hora da Estrela",
    "autor": "Clarice Lispector",
    "ano": 1977
}

```

* **O que observar:** O registro será salvo na memória e o comando de limpeza apagará a chave `"livros"` do Redis do cluster para evitar que os usuários visualizem dados defasados.

---

## 📝 Configurações de Nuvem e Variáveis de Ambiente

* **Variáveis de Ambiente**: O arquivo `main.py` utiliza `os.getenv("REDIS_HOST", "localhost")` para rodar de forma híbrida.
* **Injeção via K8s**: O arquivo `deployment.yaml` se encarrega de injetar o valor dinâmico `"redis-service"`, permitindo que o código localize o banco de cache sem configurações fixas (hardcoded).

```

```