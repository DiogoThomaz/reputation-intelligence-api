from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .routes import health, search, reviews, dashboard


def create_app() -> FastAPI:
    app = FastAPI(title="Reputation Intelligence API")
    app.include_router(health.router)
    app.include_router(search.router)
    app.include_router(reviews.router)
    app.include_router(dashboard.router)

    app.mount("/app", StaticFiles(directory="src/static", html=True), name="app")

    @app.get("/app-ui")
    def _app_ui():
        return FileResponse("src/static/index.html")
    return app


app = create_app()
