from fastapi import APIRouter, HTTPException

from app.schemas.search import SearchCreateRequest, SearchCreateResponse
from app.schemas.search_result import SearchResultResponse
from app.services.search_service import create_search, get_search

router = APIRouter()


@router.post("", response_model=SearchCreateResponse)
def create(req: SearchCreateRequest):
    sid = create_search(req.company_name)
    return {"search_id": sid, "status": "processing"}


@router.get("/{search_id}", response_model=SearchResultResponse)
def get(search_id: str):
    data = get_search(search_id)
    if not data:
        raise HTTPException(status_code=404, detail="search not found")

    return {
        "search_id": search_id,
        "status": data.get("status", "processing"),
        "company_name": data["company_name"],
        "summary": {"total_items": 0, "by_source": {}, "by_sentiment": {}},
        "items": [],
    }
