from uuid import uuid4

from sqlalchemy.orm import Session

from ..model.search import Search
from ..repository.search_repo import SearchRepository


def create_search(db: Session, repo: SearchRepository, company_name: str) -> str:
    sid = str(uuid4())
    repo.create(db, Search(id=sid, company_name=company_name, status="processing"))
    return sid


def get_search(db: Session, repo: SearchRepository, search_id: str):
    return repo.get(db, search_id)
