from uuid import uuid4

from app.domain.models import Search
from app.repositories.base import SearchRepository


def create_search(repo: SearchRepository, *, company_name: str) -> str:
    sid = str(uuid4())
    search = Search(id=sid, company_name=company_name, status="processing")
    repo.create(search=search)
    return sid


def get_search(repo: SearchRepository, *, search_id: str):
    return repo.get(search_id=search_id)
