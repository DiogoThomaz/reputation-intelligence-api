import json

from sqlalchemy.orm import Session

from ..settings import settings

from ..db import SessionLocal, Base, engine
from ..model.review_db import Review
from ..repository.review_repo import SqlAlchemyReviewRepository
from ..service.playstore import search_playstore
from ..service.ollama_client import chunk_items, classify_batch


def collect_playstore_reviews(search_id: str, app_id: str, max_reviews: int) -> None:
    # cada background task abre sua própria sessão
    Base.metadata.create_all(bind=engine)

    repo = SqlAlchemyReviewRepository()
    db: Session = SessionLocal()
    try:
        reviews = list(search_playstore(app_id, max_reviews=max_reviews))

        items = [{"id": str(i), "text": r.text} for i, r in enumerate(reviews)]
        batches = chunk_items(
            items,
            max_items=settings.ollama_batch_max_items,
            max_chars=settings.ollama_batch_max_chars,
        )

        idx = 0
        for b in batches:
            results = classify_batch(b)
            for (sentiment, tags) in results:
                r = reviews[idx]
                idx += 1

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
