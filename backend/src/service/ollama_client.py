from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

import httpx

from ..settings import settings


def _parse_json(s: str) -> dict:
    s = s.strip()
    # tenta extrair json mesmo se vier com texto extra
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        s = s[start : end + 1]
    return json.loads(s)


def _post_ollama_chat(client: httpx.Client, prompt: str) -> str:
    r = client.post(
        f"{settings.ollama_base_url}/api/chat",
        json={
            "model": settings.ollama_model,
            "messages": [
                {"role": "system", "content": "Responda apenas JSON."},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "options": {"temperature": 0.1},
        },
    )
    r.raise_for_status()
    data = r.json()
    return data.get("message", {}).get("content", "")


def _post_ollama_generate(client: httpx.Client, prompt: str) -> str:
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
    data = r.json()
    return data.get("response", "")


def _call_ollama(prompt: str) -> str:
    # Preferimos /api/chat; se falhar, tentamos /api/generate
    with httpx.Client(timeout=30.0) as client:
        try:
            return _post_ollama_chat(client, prompt)
        except Exception:
            return _post_ollama_generate(client, prompt)


def classify_text(text: str) -> Tuple[str, List[str]]:
    """Classifica sentimento + tags de intenção via Ollama.

    Retorna: (sentiment, intent_tags)
    """
    prompt = (
        "Você é um classificador. Retorne APENAS JSON válido, sem markdown, sem explicação.\n"
        "Campos obrigatórios: sentiment e intent_tags.\n"
        "sentiment deve ser exatamente um destes: positivo, neutro, negativo.\n"
        "intent_tags deve ser uma lista curta (1-4) com tags em snake_case.\n"
        "Texto:\n"
        f"{text}\n"
        "JSON:" 
    )

    content = _call_ollama(prompt)

    try:
        obj = _parse_json(content)
        sentiment = str(obj.get("sentiment", "")).strip().lower()
        tags = obj.get("intent_tags") or []
        if not isinstance(tags, list):
            tags = []
        tags = [str(t).strip() for t in tags if str(t).strip()]

        if sentiment not in {"positivo", "neutro", "negativo"}:
            sentiment = "neutro"

        return sentiment, tags
    except Exception as e:
        print("Error parsing Ollama response:", e)
        print("Original content:", content)
        return "n/a", []


def _backoff_seconds(attempt: int) -> float:
    # 0, 1, 2, 3 => 0.5, 1, 2, 4 (cap 8)
    return float(min(8.0, 0.5 * (2**attempt)))


def classify_batch(items: List[Dict[str, str]]) -> List[Tuple[str, List[str]]]:
    """Classifica um lote de textos em uma única chamada ao Ollama.

    items: [{"id": "...", "text": "..."}, ...]
    Retorna lista alinhada no mesmo tamanho: [(sentiment, tags), ...]

    Com retry + backoff e fallback (divide o batch) quando falhar.
    """

    if not items:
        return []

    prompt = (
        "Você é um classificador. Retorne APENAS JSON válido, sem markdown, sem explicação.\n"
        "Seu objetivo é classificar CADA item com sentimento e tags de intenção.\n"
        "Regras:\n"
        "- sentiment deve ser exatamente um destes: positivo, neutro, negativo.\n"
        "- intent_tags deve ser uma lista curta (1-4) com tags em snake_case.\n"
        "- Retorne no formato: {\"results\": [{\"id\":...,\"sentiment\":...,\"intent_tags\":[...]}]}\n"
        "- A quantidade de results deve ser IGUAL a quantidade de items.\n\n"
        f"items={json.dumps(items, ensure_ascii=False)}\n"
        "JSON:"
    )

    last_err: Exception | None = None
    for attempt in range(4):
        try:
            content = _call_ollama(prompt)
            obj = _parse_json(content)
            results = obj.get("results")
            if not isinstance(results, list):
                raise ValueError("missing results[]")
            if len(results) != len(items):
                raise ValueError("results length mismatch")

            out: List[Tuple[str, List[str]]] = []
            for r in results:
                if not isinstance(r, dict):
                    raise ValueError("invalid result item")
                sentiment = str(r.get("sentiment", "")).strip().lower()
                if sentiment not in {"positivo", "neutro", "negativo"}:
                    sentiment = "neutro"
                tags = r.get("intent_tags") or []
                if not isinstance(tags, list):
                    tags = []
                tags = [str(t).strip() for t in tags if str(t).strip()]
                out.append((sentiment, tags))

            return out
        except Exception as e:
            last_err = e
            import time

            time.sleep(_backoff_seconds(attempt))

    # fallback: divide o lote
    if len(items) == 1:
        # fallback final para a implementação antiga
        return [classify_text(items[0]["text"])]

    mid = len(items) // 2
    left = classify_batch(items[:mid])
    right = classify_batch(items[mid:])
    return left + right


def chunk_items(
    items: List[Dict[str, str]],
    max_items: int = 25,
    max_chars: int = 15000,
) -> List[List[Dict[str, str]]]:
    """Divide items em lotes respeitando max_items e max_chars (somatório de text)."""

    batches: List[List[Dict[str, str]]] = []
    cur: List[Dict[str, str]] = []
    cur_chars = 0

    for it in items:
        text = (it.get("text") or "")
        size = len(text)

        if cur and (len(cur) >= max_items or (cur_chars + size) > max_chars):
            batches.append(cur)
            cur = []
            cur_chars = 0

        cur.append(it)
        cur_chars += size

    if cur:
        batches.append(cur)

    return batches
