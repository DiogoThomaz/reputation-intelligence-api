from __future__ import annotations

import json
from typing import List, Tuple

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

    # Preferimos /api/chat; se falhar, tentamos /api/generate
    with httpx.Client(timeout=30.0) as client:
        try:
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
            content = data.get("message", {}).get("content", "")
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
            data = r.json()
            content = data.get("response", "")

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
