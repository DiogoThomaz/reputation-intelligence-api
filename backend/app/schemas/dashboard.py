from pydantic import BaseModel
from typing import Dict, List


class DashboardResponse(BaseModel):
    search_id: str
    sentiment_distribution: Dict[str, int]
    top_intent_tags: List[str]
    by_source: Dict[str, int]
