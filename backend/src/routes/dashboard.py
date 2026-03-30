from fastapi import APIRouter

from ..model.dashboard import DashboardResponse

router = APIRouter()


@router.get("/dashboard/{search_id}", response_model=DashboardResponse)
def get_dashboard(search_id: str):
    return {
        "search_id": search_id,
        "sentiment_distribution": {},
        "top_intent_tags": [],
        "by_source": {},
    }
