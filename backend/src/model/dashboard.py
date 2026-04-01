from __future__ import annotations

from datetime import date
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel


Sentiment = Literal["positivo", "neutro", "negativo"]
StatusLevel = Literal["ok", "atencao", "critico"]
Severity = Literal["low", "medium", "high"]


class CountPct(BaseModel):
    count: int
    pct: float


class SentimentDistribution(BaseModel):
    positivo: CountPct
    neutro: CountPct
    negativo: CountPct


class TrendMetric(BaseModel):
    current: float
    previous: float
    delta: float


class DashboardSummary(BaseModel):
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    total_reviews: int
    overall_status: StatusLevel
    risk_score: int
    sentiment: SentimentDistribution
    negative_pct_trend: TrendMetric


class ReviewExample(BaseModel):
    id: str
    rating: Optional[int] = None
    date: Optional[str] = None
    source: Optional[str] = None
    sentiment: Optional[str] = None
    intent_tags: List[str] = []
    text: str


class InsightEvidence(BaseModel):
    tag: str
    count: int
    pct: float
    negative_pct: float
    avg_rating: Optional[float] = None


class Insight(BaseModel):
    title: str
    primary_tag: str
    polarity: Literal["positive", "negative"]
    severity: Severity
    evidence: InsightEvidence
    examples: List[ReviewExample]


class TopTagItem(BaseModel):
    tag: str
    count: int
    pct: float
    negative_pct: float


class TimeSeriesPoint(BaseModel):
    bucket: str  # YYYY-MM-DD
    total: int
    negative_pct: float


class DashboardBreakdowns(BaseModel):
    by_source: Dict[str, int]
    top_tags: List[TopTagItem]
    tag_by_sentiment: Dict[str, Dict[str, int]]
    time_series: List[TimeSeriesPoint]


class DashboardResponse(BaseModel):
    search_id: str
    summary: DashboardSummary
    top_negative_insights: List[Insight]
    top_positive_insights: List[Insight]
    breakdowns: DashboardBreakdowns
