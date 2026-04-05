from __future__ import annotations

import json
from typing import Dict, List, Tuple

import httpx

from ..settings import settings
from ..model.company_profile import CompanyProfile
from .tag_normalizer import normalize_tag_list


def _parse_json(s: str) -> dict:
    s = s.strip()
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        s = s[start : end + 1]
    return json.loads(s)


def classify_review_with_profile(text: str, profile: CompanyProfile) -> Tuple[str, List[str], List[str]]:
    """Classifica: sentimento + intent_tags + product_tags, usando taxonomia do profile.

    Regras:
    - 1 sentimento
    - 0-3 intents
    - 0-3 products
    """

    intent_ids = [t.id for t in profile.intents][:20]
    prod_ids = [t.id for t in profile.products][:20]

    # keep prompt short: only ids + a few aliases
    intents_compact = [
        {"id": t.id, "aliases": t.aliases[:4]} for t in profile.intents[:20]
    ]
    products_compact = [
        {"id": t.id, "aliases": t.aliases[:4]} for t in profile.products[:20]
    ]

    prompt = (
        "Você é um classificador de reviews de aplicativo. Retorne APENAS JSON válido, sem markdown.\n"
        "Campos obrigatórios: sentiment, intent_tags, product_tags.\n"
        "Regras:\n"
        "- sentiment: positivo|neutro|negativo\n"
        "- intent_tags: 0-3 itens, SOMENTE ids presentes em intents (ou vazio)\n"
        "- product_tags: 0-3 itens, SOMENTE ids presentes em products (ou vazio)\n"
        "- Se não tiver certeza, retorne listas vazias.\n\n"
        f"company_name={profile.company_name}\n"
        f"sector={profile.sector or ''}\n"
        f"size={profile.size or ''}\n\n"
        f"intents={json.dumps(intents_compact, ensure_ascii=False)}\n"
        f"products={json.dumps(products_compact, ensure_ascii=False)}\n\n"
        "Review:\n"
        f"{text}\n\n"
        "JSON:"
    )

    with httpx.Client(timeout=60.0) as client:
        try:
            r = client.post(
                f"{settings.ollama_base_url}/api/chat",
                json={
                    "model": settings.ollama_model,
                    "messages": [
                        {"role": "system", "content": "Responda apenas JSON válido."},
                        {"role": "user", "content": prompt},
                    ],
                    "stream": False,
                    "options": {"temperature": 0.1},
                },
            )
            r.raise_for_status()
            content = r.json().get("message", {}).get("content", "")
        except Exception:
            r = client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1},
                },
            )
            r.raise_for_status()
            content = r.json().get("response", "")

    obj = _parse_json(content)

    sentiment = str(obj.get("sentiment", "")).strip().lower()
    if sentiment not in {"positivo", "neutro", "negativo"}:
        sentiment = "neutro"

    intents = obj.get("intent_tags") or []
    if not isinstance(intents, list):
        intents = []
    prods = obj.get("product_tags") or []
    if not isinstance(prods, list):
        prods = []

    intents = normalize_tag_list(intents, max_items=3)
    prods = normalize_tag_list(prods, max_items=3)

    # enforce closed set
    intents = [t for t in intents if t in intent_ids]
    prods = [p for p in prods if p in prod_ids]

    return sentiment, intents, prods
