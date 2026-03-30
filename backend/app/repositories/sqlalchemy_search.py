from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.domain.models import Search
from app.repositories.base import SearchRepository


class SqlAlchemySearchRepository(SearchRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(self, *, search: Search) -> None:
        self.db.add(search)
        self.db.commit()

    def get(self, *, search_id: str) -> Optional[Search]:
        return self.db.get(Search, search_id)
