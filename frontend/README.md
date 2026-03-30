# Frontend (HTML + JS)

Página única para iniciar uma pesquisa e acompanhar os resultados em tempo real.

## Como usar

1) Rode o backend:

```bash
cd backend
uvicorn src.app:app --reload --port 8000
```

2) Abra o `frontend/index.html` no navegador.

Se a API não estiver em `http://localhost:8000`, passe na URL:

```
index.html?api=http://SEU_HOST:8000
```

> Observação: pode haver bloqueio de CORS se você abrir via `file://`.
> Se isso acontecer, sirva a pasta `frontend/` com um servidor estático simples.
