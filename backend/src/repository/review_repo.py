from abc import ABC, abstractmethod
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..model.review_db import Review


class ReviewRepository(ABC):
    @abstractmethod
    def add(self, db: Session, review: Review) -> None: ...

    @abstractmethod
    def list_by_search(self, db: Session, search_id: str) -> List[Review]: ...


class SqlAlchemyReviewRepository(ReviewRepository):
    def add(self, db: Session, review: Review) -> None:
        db.add(review)
        db.commit()

    def list_by_search(self, db: Session, search_id: str) -> List[Review]:
        return list(db.scalars(select(Review).where(Review.search_id == search_id)).all())
