import json

from sqlalchemy.orm import Session

from ..settings import settings

from ..db import SessionLocal, Base, engine
from ..model.review_db import Review
from ..repository.review_repo import SqlAlchemyReviewRepository
from ..service.playstore import search_playstore
from ..service.ollama_client import classify_text


def collect_playstore_reviews(search_id: str, app_id: str, max_reviews: int) -> None:
    # cada background task abre sua própria sessão
    Base.metadata.create_all(bind=engine)

    repo = SqlAlchemyReviewRepository()
    db: Session = SessionLocal()
    try:
        for r in search_playstore(app_id, max_reviews=max_reviews):
            sentiment, tags = classify_text(r.text)

            review = Review(
                search_id=search_id,
                source=r.source,
                rating=r.rating,
                date=r.date,
                author=r.author,
                text=r.text,
                sentiment=sentiment,
                intent_tags=json.dumps(tags, ensure_ascii=False),
                ai_model=settings.ollama_model,
            )
            repo.add(db, review)
    finally:
        db.close()
