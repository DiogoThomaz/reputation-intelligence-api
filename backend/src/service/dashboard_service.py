import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from sqlalchemy.orm import Session

from ..model.review_db import Review
from .dashboard_products import compute_product_breakdowns


@dataclass
class DashboardResult:
    period_start: Optional[str]
    period_end: Optional[str]
    total_reviews: int
    overall_status: str
    risk_score: int
    sentiment: Dict[str, Dict[str, float]]
    negative_pct_trend: Dict[str, float]
    by_source: Dict[str, int]
    top_tags: List[Dict[str, Any]]
    tag_by_sentiment: Dict[str, Dict[str, int]]
    time_series: List[Dict[str, Any]]
    top_negative_insights: List[Dict[str, Any]]
    top_positive_insights: List[Dict[str, Any]]


def _safe_json_list(s: Any) -> List[str]:
    if s is None:
        return []
    if isinstance(s, list):
        return [str(x) for x in s if str(x).strip()]
    if isinstance(s, str):
        raw = s.strip()
        if not raw:
            return []
        try:
            val = json.loads(raw)
            if isinstance(val, list):
                return [str(x) for x in val if str(x).strip()]
        except Exception:
            return []
    return []


def _parse_date(s: Any) -> Optional[pd.Timestamp]:
    if s is None:
        return None
    if isinstance(s, (datetime, pd.Timestamp)):
        return pd.to_datetime(s)
    if isinstance(s, str):
        raw = s.strip()
        if not raw:
            return None
        # best-effort parse (playstore scraper may give different formats)
        try:
            return pd.to_datetime(raw, errors="coerce", utc=False)
        except Exception:
            return None
    return None


def _norm_sentiment(s: Any) -> str:
    if not s:
        return ""
    v = str(s).strip().lower()
    # allow aliases
    if v in {"positive", "positivo"}:
        return "positivo"
    if v in {"neutral", "neutro"}:
        return "neutro"
    if v in {"negative", "negativo"}:
        return "negativo"
    return v


def _pct(n: float, d: float) -> float:
    if d <= 0:
        return 0.0
    return float(n) / float(d)


def _severity_from_negative_pct(neg_pct: float) -> str:
    # simple and explainable
    if neg_pct >= 0.60:
        return "high"
    if neg_pct >= 0.35:
        return "medium"
    return "low"


def _status_from_risk(risk: int) -> str:
    if risk >= 70:
        return "critico"
    if risk >= 40:
        return "atencao"
    return "ok"


def build_dashboard(db: Session, search_id: str, window_days: int = 30) -> DashboardResult:
    rows: List[Review] = db.query(Review).filter(Review.search_id == search_id).all()

    if not rows:
        empty_sent = {
            "positivo": {"count": 0, "pct": 0.0},
            "neutro": {"count": 0, "pct": 0.0},
            "negativo": {"count": 0, "pct": 0.0},
        }
        return DashboardResult(
            period_start=None,
            period_end=None,
            total_reviews=0,
            overall_status="ok",
            risk_score=0,
            sentiment=empty_sent,
            negative_pct_trend={"current": 0.0, "previous": 0.0, "delta": 0.0},
            by_source={},
            top_tags=[],
            tag_by_sentiment={},
            time_series=[],
            top_negative_insights=[],
            top_positive_insights=[],
        )

    df = pd.DataFrame(
        [
            {
                "id": str(r.id),
                "source": r.source,
                "rating": r.rating,
                "date": _parse_date(r.date),
                "sentiment": _norm_sentiment(r.sentiment),
                "intent_tags": _safe_json_list(r.intent_tags),
                "product_tags": _safe_json_list(getattr(r, "product_tags", None)),
                "text": r.text,
            }
            for r in rows
        ]
    )

    # Clean
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    has_date = df["date"].notna().any()

    # Determine period using available dates; otherwise treat all as current window
    if has_date:
        period_end_ts = df["date"].max()
        period_start_ts = period_end_ts - pd.Timedelta(days=window_days)
        current_df = df[(df["date"] >= period_start_ts) & (df["date"] <= period_end_ts)]
        prev_start_ts = period_start_ts - pd.Timedelta(days=window_days)
        prev_df = df[(df["date"] >= prev_start_ts) & (df["date"] < period_start_ts)]
        period_start = period_start_ts.date().isoformat() if pd.notna(period_start_ts) else None
        period_end = period_end_ts.date().isoformat() if pd.notna(period_end_ts) else None
    else:
        current_df = df
        prev_df = df.iloc[0:0]
        period_start = None
        period_end = None

    total = int(len(current_df))

    # By source
    by_source = current_df["source"].value_counts(dropna=False).to_dict()
    by_source = {str(k): int(v) for k, v in by_source.items()}

    # Sentiment distribution (on current window)
    sentiments = ["positivo", "neutro", "negativo"]
    sent_counts = current_df["sentiment"].value_counts().to_dict()
    sent_out: Dict[str, Dict[str, float]] = {}
    for s in sentiments:
        c = int(sent_counts.get(s, 0))
        sent_out[s] = {"count": c, "pct": _pct(c, total)}

    # Trend: negative pct current vs previous
    cur_neg_pct = _pct(int((current_df["sentiment"] == "negativo").sum()), max(1, len(current_df)))
    prev_neg_pct = _pct(int((prev_df["sentiment"] == "negativo").sum()), max(1, len(prev_df))) if len(prev_df) else 0.0
    neg_trend = {"current": float(cur_neg_pct), "previous": float(prev_neg_pct), "delta": float(cur_neg_pct - prev_neg_pct)}

    # Tags exploded
    tag_df = current_df[["id", "sentiment", "rating", "source", "date", "text", "intent_tags"]].copy()
    tag_df = tag_df.explode("intent_tags")
    tag_df["intent_tags"] = tag_df["intent_tags"].fillna("")
    tag_df = tag_df[tag_df["intent_tags"].astype(str).str.len() > 0]

    # Top tags with counts + negative_pct
    if len(tag_df):
        tag_counts = tag_df["intent_tags"].value_counts().head(10)
        top_tags: List[Dict[str, Any]] = []
        for tag, cnt in tag_counts.items():
            tag_rows = tag_df[tag_df["intent_tags"] == tag]
            neg_pct = _pct(int((tag_rows["sentiment"] == "negativo").sum()), max(1, len(tag_rows)))
            top_tags.append(
                {
                    "tag": str(tag),
                    "count": int(cnt),
                    "pct": _pct(int(cnt), total),
                    "negative_pct": float(neg_pct),
                }
            )
    else:
        top_tags = []

    # Tag by sentiment matrix
    tag_by_sentiment: Dict[str, Dict[str, int]] = {}
    if len(tag_df):
        pivot = pd.pivot_table(
            tag_df,
            index="intent_tags",
            columns="sentiment",
            values="id",
            aggfunc="count",
            fill_value=0,
        )
        for tag, row in pivot.iterrows():
            tag_by_sentiment[str(tag)] = {s: int(row.get(s, 0)) for s in sentiments}

    # Time series (daily buckets) for current window
    time_series: List[Dict[str, Any]] = []
    if has_date and len(current_df):
        ts = current_df.copy()
        ts["bucket"] = ts["date"].dt.date.astype(str)
        grp = ts.groupby("bucket")
        for bucket, g in grp:
            neg_pct = _pct(int((g["sentiment"] == "negativo").sum()), max(1, len(g)))
            time_series.append({"bucket": str(bucket), "total": int(len(g)), "negative_pct": float(neg_pct)})
        time_series.sort(key=lambda x: x["bucket"])

    # Insights: score tags to pick 3 negative + 3 positive
    def tag_metrics(tag: str) -> Tuple[int, float, float, Optional[float]]:
        if not len(tag_df):
            return (0, 0.0, 0.0, None)
        tr = tag_df[tag_df["intent_tags"] == tag]
        cnt = int(len(tr))
        pct = _pct(cnt, total)
        neg_pct = _pct(int((tr["sentiment"] == "negativo").sum()), max(1, len(tr)))
        avg_rating = float(tr["rating"].mean()) if tr["rating"].notna().any() else None
        return (cnt, float(pct), float(neg_pct), avg_rating)

    def tag_examples(tag: str, polarity: str) -> List[Dict[str, Any]]:
        if not len(tag_df):
            return []
        tr = tag_df[tag_df["intent_tags"] == tag]
        if polarity == "negative":
            tr = tr.sort_values(by=["sentiment", "rating"], ascending=[True, True])
        else:
            tr = tr.sort_values(by=["sentiment", "rating"], ascending=[True, False])
        ex = []
        # get unique reviews
        seen = set()
        for _, r in tr.iterrows():
            rid = str(r["id"])
            if rid in seen:
                continue
            seen.add(rid)
            text = str(r["text"])
            ex.append(
                {
                    "id": rid,
                    "rating": int(r["rating"]) if pd.notna(r["rating"]) else None,
                    "date": r["date"].date().isoformat() if pd.notna(r["date"]) else None,
                    "source": str(r["source"]),
                    "sentiment": str(r["sentiment"]),
                    "intent_tags": [str(tag)],
                    "text": text[:400],
                }
            )
            if len(ex) >= 3:
                break
        return ex

    negative_candidates = []
    positive_candidates = []
    for t in top_tags:
        tag = t["tag"]
        cnt, pct, neg_pct, avg_rating = tag_metrics(tag)
        # scoring: weight prevalence and negativity/positivity
        neg_score = pct * 0.6 + neg_pct * 0.4
        pos_score = pct * 0.6 + (1.0 - neg_pct) * 0.4
        negative_candidates.append((neg_score, tag, cnt, pct, neg_pct, avg_rating))
        positive_candidates.append((pos_score, tag, cnt, pct, neg_pct, avg_rating))

    negative_candidates.sort(reverse=True)
    positive_candidates.sort(reverse=True)

    top_negative_insights: List[Dict[str, Any]] = []
    for _, tag, cnt, pct, neg_pct, avg_rating in negative_candidates[:3]:
        top_negative_insights.append(
            {
                "title": f"Alerta: {tag}",
                "primary_tag": tag,
                "polarity": "negative",
                "severity": _severity_from_negative_pct(neg_pct),
                "evidence": {
                    "tag": tag,
                    "count": int(cnt),
                    "pct": float(pct),
                    "negative_pct": float(neg_pct),
                    "avg_rating": avg_rating,
                },
                "examples": tag_examples(tag, "negative"),
            }
        )

    top_positive_insights: List[Dict[str, Any]] = []
    for _, tag, cnt, pct, neg_pct, avg_rating in positive_candidates[:3]:
        top_positive_insights.append(
            {
                "title": f"Destaque: {tag}",
                "primary_tag": tag,
                "polarity": "positive",
                "severity": "low",
                "evidence": {
                    "tag": tag,
                    "count": int(cnt),
                    "pct": float(pct),
                    "negative_pct": float(neg_pct),
                    "avg_rating": avg_rating,
                },
                "examples": tag_examples(tag, "positive"),
            }
        )

    # Risk score: simple, explainable
    # Combine negative_pct, and negative trend delta
    risk = int(round(min(100.0, max(0.0, (cur_neg_pct * 100.0) * 0.8 + max(0.0, neg_trend["delta"]) * 100.0 * 0.2))))
    overall_status = _status_from_risk(risk)

    prod = compute_product_breakdowns(current_df)

    # attach to breakdowns by storing on the result object (kept as dicts)
    # We'll pass through via routes.

    res = DashboardResult(
        period_start=period_start,
        period_end=period_end,
        total_reviews=total,
        overall_status=overall_status,
        risk_score=risk,
        sentiment=sent_out,
        negative_pct_trend=neg_trend,
        by_source=by_source,
        top_tags=top_tags,
        tag_by_sentiment=tag_by_sentiment,
        time_series=time_series,
        top_negative_insights=top_negative_insights,
        top_positive_insights=top_positive_insights,
    )

    # dynamic attrs (simple for now)
    setattr(res, "top_products", prod.get("top_products", []))
    setattr(res, "product_by_sentiment", prod.get("product_by_sentiment", {}))

    return res
