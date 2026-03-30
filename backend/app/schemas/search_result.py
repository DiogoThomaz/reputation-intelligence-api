from pydantic import BaseModel
from typing import Any, Dict, List

from app.schemas.review import ReviewItem


class SearchResultResponse(BaseModel):
    search_id: str
    status: str
    company_name: str
    summary: Dict[str, Any]
    items: List[ReviewItem]
