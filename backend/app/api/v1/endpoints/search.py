from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.sqlalchemy_search import SqlAlchemySearchRepository
from app.schemas.search import SearchCreateRequest, SearchCreateResponse
from app.schemas.search_result import SearchResultResponse
from app.services.search_service import create_search, get_search

router = APIRouter()


@router.post("", response_model=SearchCreateResponse)
def create(req: SearchCreateRequest, db: Session = Depends(get_db)):
    repo = SqlAlchemySearchRepository(db)
    sid = create_search(repo, company_name=req.company_name)
    return {"search_id": sid, "status": "processing"}


@router.get("/{search_id}", response_model=SearchResultResponse)
def get(search_id: str, db: Session = Depends(get_db)):
    repo = SqlAlchemySearchRepository(db)
    search = get_search(repo, search_id=search_id)
    if not search:
        raise HTTPException(status_code=404, detail="search not found")

    return {
        "search_id": search.id,
        "status": search.status,
        "company_name": search.company_name,
        "summary": {"total_items": 0, "by_source": {}, "by_sentiment": {}},
        "items": [],
    }
