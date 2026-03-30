from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import Base, engine
from ..model.search import SearchCreateRequest, SearchCreateResponse
from ..model.search_result import SearchResultResponse
from ..repository.search_repo import SqlAlchemySearchRepository
from ..service.search_service import create_search, get_search
from .deps import get_db

router = APIRouter()
repo = SqlAlchemySearchRepository()


@router.post("/search", response_model=SearchCreateResponse)
def create(req: SearchCreateRequest, db: Session = Depends(get_db)):
    Base.metadata.create_all(bind=engine)
    sid = create_search(db, repo, req.company_name)
    return {"search_id": sid, "status": "processing"}


@router.get("/search/{search_id}", response_model=SearchResultResponse)
def get(search_id: str, db: Session = Depends(get_db)):
    Base.metadata.create_all(bind=engine)
    s = get_search(db, repo, search_id)
    if not s:
        raise HTTPException(status_code=404, detail="search not found")

    return {
        "search_id": s.id,
        "status": s.status,
        "company_name": s.company_name,
        "summary": {"total_items": 0, "by_source": {}, "by_sentiment": {}},
        "items": [],
    }
