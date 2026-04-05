from pydantic import BaseModel
from typing import List, Optional


class ReviewItem(BaseModel):
    id: str
    company_name: str
    source: str
    sentiment: str
    intent_tags: List[str]
    product_tags: List[str] = []
    comment_text: str
    rating: Optional[int] = None
    date: str
