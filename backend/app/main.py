from fastapi import FastAPI

from app.api.v1.router import api_router
from app.db.init_db import init_db


def create_app() -> FastAPI:
    app = FastAPI(title="Reputation Intelligence API")

    @app.on_event("startup")
    def _startup() -> None:
        init_db()

    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
