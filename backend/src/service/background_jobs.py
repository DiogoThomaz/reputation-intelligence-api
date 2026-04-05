import json

from sqlalchemy.orm import Session

from ..settings import settings

from ..db import SessionLocal, Base, engine
from ..model.review_db import Review
from ..repository.review_repo import SqlAlchemyReviewRepository
from ..service.playstore import search_playstore
from ..service.company_profile_service import build_company_profile
from ..service.review_classifier import classify_review_with_profile


def collect_playstore_reviews(search_id: str, app_id: str, max_reviews: int) -> None:
    # cada background task abre sua própria sessão
    Base.metadata.create_all(bind=engine)

    repo = SqlAlchemyReviewRepository()
    db: Session = SessionLocal()
    try:
        reviews = list(search_playstore(app_id, max_reviews=max_reviews))

        # 1) Gera contexto/perfil da empresa e taxonomia (0-20 intents, 0-20 products)
        sample_texts = [r.text for r in reviews[:60]]
        # Aqui não temos acesso ao company_name informado no search dentro deste job,
        # então usamos uma string vazia (o perfil é guiado principalmente pelas reviews + app_id).
        profile = build_company_profile(company_name="", app_id=app_id, sample_texts=sample_texts)
        # company_name não vem do PlayStore aqui; usamos o que o usuário informou no Search (quando disponível)
        # Mantemos vazio por enquanto e preenchemos abaixo ao salvar

        # 2) Classifica cada review com o profile (closed set) e normaliza tags
        for r in reviews:
            sentiment, intent_tags, product_tags = classify_review_with_profile(r.text, profile)

            review = Review(
                search_id=search_id,
                source=r.source,
                rating=r.rating,
                date=r.date,
                author=r.author,
                text=r.text,
                sentiment=sentiment,
                intent_tags=json.dumps(intent_tags, ensure_ascii=False),
                product_tags=json.dumps(product_tags, ensure_ascii=False),
                ai_model=settings.ollama_model,
            )
            repo.add(db, review)
    finally:
        db.close()
