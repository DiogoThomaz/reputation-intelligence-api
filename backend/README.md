# Backend (FastAPI)

## Rodar localmente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API docs:
- http://localhost:8000/docs
- http://localhost:8000/redoc
