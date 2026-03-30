from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from pathlib import Path

from .routes import health, search, reviews, dashboard


def create_app() -> FastAPI:
    app = FastAPI(title="Reputation Intelligence API")

    app.include_router(health.router)
    app.include_router(search.router)
    app.include_router(reviews.router)
    app.include_router(dashboard.router)

    # Static UI em /app
    # Resolve caminho absoluto para funcionar no Docker/uvicorn --app-dir
    static_dir = Path(__file__).resolve().parent / "static"
    if static_dir.exists():
        app.mount("/app", StaticFiles(directory=str(static_dir), html=True), name="app")

    return app


app = create_app()
