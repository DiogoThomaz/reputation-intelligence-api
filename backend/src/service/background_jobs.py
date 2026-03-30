from sqlalchemy.orm import Session

from ..db import SessionLocal, Base, engine
from ..model.review_db import Review
from ..repository.review_repo import SqlAlchemyReviewRepository
from ..service.playstore import search_playstore


def collect_playstore_reviews(search_id: str, app_id: str, max_reviews: int) -> None:
    # cada background task abre sua própria sessão
    Base.metadata.create_all(bind=engine)

    repo = SqlAlchemyReviewRepository()
    db: Session = SessionLocal()
    try:
        for r in search_playstore(app_id, max_reviews=max_reviews):
            repo.add(
                db,
                Review(
                    search_id=search_id,
                    source=r.source,
                    rating=r.rating,
                    date=r.date,
                    author=r.author,
                    text=r.text,
                ),
            )
    finally:
        db.close()
