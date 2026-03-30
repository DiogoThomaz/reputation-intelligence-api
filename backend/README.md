# Backend (FastAPI)

Arquitetura simples com pastas `src/`.

## Rodar localmente

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.app:app --reload --port 8000
```

Docs:
- http://localhost:8000/docs
