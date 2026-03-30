from fastapi import APIRouter, Query
from typing import List, Optional

from app.schemas.review import ReviewItem

router = APIRouter()


@router.get("", response_model=List[ReviewItem])
def list_reviews(
    search_id: str = Query(...),
    source: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
):
    # MVP: sem persistência real ainda
    return []
