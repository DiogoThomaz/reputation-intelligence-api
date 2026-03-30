from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from ..model.review_db import Review


class ReviewRepository(ABC):
    @abstractmethod
    def add(self, db: Session, review: Review) -> None: ...


class SqlAlchemyReviewRepository(ReviewRepository):
    def add(self, db: Session, review: Review) -> None:
        db.add(review)
        db.commit()
