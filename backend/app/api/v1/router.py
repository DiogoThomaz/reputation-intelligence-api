from fastapi import APIRouter
from app.api.v1.endpoints import health, search, reviews, dashboard

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
