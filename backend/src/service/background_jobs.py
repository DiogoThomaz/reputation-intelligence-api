import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlalchemy.orm import Session

from ..settings import settings

from ..db import SessionLocal, Base, engine
from ..model.review_db import Review
from ..repository.review_repo import SqlAlchemyReviewRepository
from ..service.playstore import search_playstore
from typing import Dict

from ..service.ollama_client import classify_batch


def collect_playstore_reviews(search_id: str, app_id: str, max_reviews: int) -> None:
    # cada background task abre sua própria sessão
    Base.metadata.create_all(bind=engine)

    repo = SqlAlchemyReviewRepository()
    db: Session = SessionLocal()
    try:
        reviews = list(search_playstore(app_id, max_reviews=max_reviews))

        # Apenas paralelismo (3 em paralelo), sem chunking.
        # ATENÇÃO: isso cria 1 request por review.
        results: List[tuple[str, list[str]]] = [("n/a", [])] * len(reviews)

        with ThreadPoolExecutor(max_workers=3) as ex:
            futs = {
                ex.submit(classify_batch, [{"id": str(i), "text": r.text}]): i
                for i, r in enumerate(reviews)
            }
            for fut in as_completed(futs):
                i = futs[fut]
                r = fut.result()
                # classify_batch retorna lista alinhada (aqui sempre 1 item)
                results[i] = r[0] if r else ("n/a", [])

        for r, (sentiment, tags) in zip(reviews, results):
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
