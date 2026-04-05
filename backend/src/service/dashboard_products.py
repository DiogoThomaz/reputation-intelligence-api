from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd


def compute_product_breakdowns(current_df: pd.DataFrame) -> Dict[str, Any]:
    """Compute top_products and product_by_sentiment using product_tags field.

    Expects columns: id, sentiment, product_tags
    """

    sentiments = ["positivo", "neutro", "negativo"]
    total = int(len(current_df))

    prod_df = current_df[["id", "sentiment", "product_tags"]].copy()
    prod_df = prod_df.explode("product_tags")
    prod_df["product_tags"] = prod_df["product_tags"].fillna("")
    prod_df = prod_df[prod_df["product_tags"].astype(str).str.len() > 0]

    if not len(prod_df):
        return {"top_products": [], "product_by_sentiment": {}}

    counts = prod_df["product_tags"].value_counts().head(10)

    top_products: List[Dict[str, Any]] = []
    for prod, cnt in counts.items():
        rows = prod_df[prod_df["product_tags"] == prod]
        neg_pct = (rows["sentiment"] == "negativo").sum() / max(1, len(rows))
        top_products.append(
            {
                "tag": str(prod),
                "count": int(cnt),
                "pct": float(int(cnt) / max(1, total)),
                "negative_pct": float(neg_pct),
            }
        )

    pivot = pd.pivot_table(
        prod_df,
        index="product_tags",
        columns="sentiment",
        values="id",
        aggfunc="count",
        fill_value=0,
    )
    product_by_sentiment: Dict[str, Dict[str, int]] = {}
    for prod, row in pivot.iterrows():
        product_by_sentiment[str(prod)] = {s: int(row.get(s, 0)) for s in sentiments}

    return {"top_products": top_products, "product_by_sentiment": product_by_sentiment}
