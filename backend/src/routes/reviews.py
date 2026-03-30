import json

from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from sqlalchemy.orm import Session

from ..db import Base, engine
from ..model.review import ReviewItem
from ..repository.review_repo import SqlAlchemyReviewRepository
from .deps import get_db

router = APIRouter()
repo = SqlAlchemyReviewRepository()


@router.get("/reviews", response_model=List[ReviewItem])
def list_reviews(
    search_id: str = Query(...),
    source: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    Base.metadata.create_all(bind=engine)
    items = repo.list_by_search(db, search_id)

    out: List[ReviewItem] = []
    for it in items:
        if source and it.source != source:
            continue
        out.append(
            ReviewItem(
                id=str(it.id),
                company_name="",
                source=it.source,
                sentiment=(it.sentiment or ""),
                intent_tags=(json.loads(it.intent_tags) if it.intent_tags else []),
                comment_text=it.text,
                rating=it.rating,
                date=it.date,
            )
        )
    return out
