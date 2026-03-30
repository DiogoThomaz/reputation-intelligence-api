# Backend (FastAPI) — Clean-ish Architecture (simples)

## Estrutura

- `app/main.py`: cria o FastAPI e registra routers
- `app/api/v1/`: camada de transporte (HTTP)
- `app/schemas/`: contratos (Pydantic)
- `app/services/`: regras de aplicação (use cases)
- `app/repositories/`: persistência (in-memory no MVP)

## Rodar localmente

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Docs:
- http://localhost:8000/docs
