import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlalchemy.orm import Session

from ..settings import settings

from ..db import SessionLocal, Base, engine
from ..model.review_db import Review
from ..repository.review_repo import SqlAlchemyReviewRepository
from ..service.playstore import search_playstore
from typing import Dict

from ..service.ollama_client import chunk_items, classify_batch


def collect_playstore_reviews(search_id: str, app_id: str, max_reviews: int) -> None:
    # cada background task abre sua própria sessão
    Base.metadata.create_all(bind=engine)

    repo = SqlAlchemyReviewRepository()
    db: Session = SessionLocal()
    try:
        reviews = list(search_playstore(app_id, max_reviews=max_reviews))

        items = [{"id": str(i), "text": r.text} for i, r in enumerate(reviews)]
        batches = chunk_items(items, max_items=5, max_chars=2000)

        # Processa batches em paralelo (limitado) para reduzir tempo total.
        # Cada batch tem backoff + fallback dentro do classify_batch.
        results_by_batch: Dict[int, List[tuple[str, list[str]]]] = {}

        with ThreadPoolExecutor(max_workers=3) as ex:
            futs = {ex.submit(classify_batch, b): i for i, b in enumerate(batches)}
            for fut in as_completed(futs):
                i = futs[fut]
                results_by_batch[i] = fut.result()

        idx = 0
        for i in range(len(batches)):
            results = results_by_batch.get(i) or []
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
