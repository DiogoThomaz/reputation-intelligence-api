from fastapi import FastAPI

from .routes import health, search, reviews, dashboard


def create_app() -> FastAPI:
    app = FastAPI(title="Reputation Intelligence API")
    app.include_router(health.router)
    app.include_router(search.router)
    app.include_router(reviews.router)
    app.include_router(dashboard.router)
    return app


app = create_app()
