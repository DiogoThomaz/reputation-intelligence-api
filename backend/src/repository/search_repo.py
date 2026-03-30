from abc import ABC, abstractmethod
from typing import Optional

from sqlalchemy.orm import Session

from ..model.search import Search


class SearchRepository(ABC):
    @abstractmethod
    def create(self, db: Session, search: Search) -> None: ...

    @abstractmethod
    def get(self, db: Session, search_id: str) -> Optional[Search]: ...


class SqlAlchemySearchRepository(SearchRepository):
    def create(self, db: Session, search: Search) -> None:
        db.add(search)
        db.commit()

    def get(self, db: Session, search_id: str) -> Optional[Search]:
        return db.get(Search, search_id)
