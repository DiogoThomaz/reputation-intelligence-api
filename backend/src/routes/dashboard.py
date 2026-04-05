from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..model.dashboard import DashboardResponse
from ..service.dashboard_service import build_dashboard
from .deps import get_db

router = APIRouter()


@router.get("/dashboard/{search_id}", response_model=DashboardResponse)
def get_dashboard(search_id: str, db: Session = Depends(get_db)):
    r = build_dashboard(db, search_id)

    return {
        "search_id": search_id,
        "summary": {
            "period_start": r.period_start,
            "period_end": r.period_end,
            "total_reviews": r.total_reviews,
            "overall_status": r.overall_status,
            "risk_score": r.risk_score,
            "sentiment": r.sentiment,
            "negative_pct_trend": r.negative_pct_trend,
        },
        "top_negative_insights": r.top_negative_insights,
        "top_positive_insights": r.top_positive_insights,
        "breakdowns": {
            "by_source": r.by_source,
            "top_tags": r.top_tags,
            "tag_by_sentiment": r.tag_by_sentiment,
            "time_series": r.time_series,
            "top_products": getattr(r, "top_products", []),
            "product_by_sentiment": getattr(r, "product_by_sentiment", {}),
        },
    }
