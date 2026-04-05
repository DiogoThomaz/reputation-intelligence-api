from __future__ import annotations

import json
from typing import List

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


def build_company_profile(company_name: str, app_id: str | None, sample_texts: List[str]) -> CompanyProfile:
    """Gera um perfil de empresa (setor/tamanho/produtos/intenções) via LLM.

    - products: 0-20
    - intents: 0-20
    - tags normalizadas em snake_case sem acento
    """

    sample = "\n\n".join(f"- {t[:240]}" for t in sample_texts[:30] if t)

    prompt = (
        "Você é um analista de produto e atendimento.\n"
        "Crie um perfil objetivo da empresa e do app a partir de amostras de reviews.\n"
        "Retorne APENAS JSON válido, sem markdown.\n\n"
        f"company_name={company_name}\n"
        f"playstore_app_id={app_id or ''}\n\n"
        "Amostra de reviews (pode conter ruído):\n"
        f"{sample}\n\n"
        "Regras de saída:\n"
        "- sector: string curta (ex: banco, varejo, mobilidade, saude, telecom) ou null\n"
        "- size: micro|pequena|media|grande|enterprise|unknown\n"
        "- products: lista 0-20 itens; cada item tem id (snake_case, sem acento), label (PT-BR), aliases (0-6)\n"
        "- intents: lista 0-20 itens; cada item tem id (snake_case, sem acento), label (PT-BR), aliases (0-6)\n"
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

    # Normalize ids post-hoc (defensive)
    def norm_defs(defs: list) -> list:
        out = []
        for d in defs or []:
            if not isinstance(d, dict):
                continue
            _id = d.get("id") or ""
            _label = d.get("label") or ""
            aliases = d.get("aliases") or []
            if not isinstance(aliases, list):
                aliases = []
            norm_id = normalize_tag_list([_id], max_items=1)
            if not norm_id:
                continue
            out.append(
                {
                    "id": norm_id[0],
                    "label": str(_label).strip()[:80],
                    "aliases": [str(a).strip()[:40] for a in aliases[:6] if str(a).strip()],
                }
            )
            if len(out) >= 20:
                break
        return out

    obj["company_name"] = company_name
    obj["products"] = norm_defs(obj.get("products") or [])
    obj["intents"] = norm_defs(obj.get("intents") or [])

    return CompanyProfile.model_validate(obj)
