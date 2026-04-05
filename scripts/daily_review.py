#!/usr/bin/env python3
"""Daily product+engineering review for reputation-intelligence-api.

Runs locally on the OpenClaw host. Prints a Telegram-ready message.

No network writes. Safe to run from cron.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

REPO_DIR = Path(__file__).resolve().parents[1]
TZ = os.getenv("TZ", "America/Sao_Paulo")


def sh(cmd: List[str], cwd: Path = REPO_DIR, timeout: int = 15) -> Tuple[int, str]:
    try:
        p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=timeout)
        out = (p.stdout or "") + ("\n" + p.stderr if p.stderr else "")
        return p.returncode, out.strip()
    except Exception as e:
        return 1, f"error running {cmd}: {e}"


def git_recent_commits(n: int = 8) -> str:
    code, out = sh(["git", "log", f"-n{n}", "--pretty=format:%h %s (%cr)"])
    if code != 0 or not out:
        return "(sem dados)"
    return out


def git_changed_files(since: str = "yesterday") -> str:
    # best-effort: last 24h
    code, out = sh(["git", "log", "--since=24.hours", "--name-only", "--pretty=format:"], timeout=30)
    if code != 0:
        return "(sem dados)"
    files = sorted({f.strip() for f in out.splitlines() if f.strip()})
    if not files:
        return "(nenhuma mudança nas últimas 24h)"
    return "\n".join(f"- {f}" for f in files[:30]) + ("\n- ..." if len(files) > 30 else "")


def repo_health_notes() -> List[str]:
    notes: List[str] = []

    # Quick static sanity checks
    backend = REPO_DIR / "backend"
    if not backend.exists():
        notes.append("Backend: pasta backend/ não encontrada (verificar estrutura do repo).")
        return notes

    # Check key files
    must = [
        backend / "src" / "routes" / "dashboard.py",
        backend / "src" / "service" / "background_jobs.py",
        backend / "src" / "service" / "ollama_client.py",
        backend / "src" / "static" / "index.html",
        backend / "src" / "static" / "app.js",
    ]
    missing = [str(p.relative_to(REPO_DIR)) for p in must if not p.exists()]
    if missing:
        notes.append("Arquivos esperados ausentes: " + ", ".join(missing))

    # Try python compile (if python3 exists)
    code, _ = sh(["bash", "-lc", "command -v python3 >/dev/null 2>&1 && echo OK || echo NO"], timeout=5)
    # code here is always 0; rely on output
    _, has = sh(["bash", "-lc", "command -v python3 >/dev/null 2>&1 && echo yes || echo no"], timeout=5)
    if has.strip() == "yes":
        code, out = sh(["bash", "-lc", "python3 -m py_compile backend/src/service/ollama_client.py backend/src/service/background_jobs.py backend/src/service/dashboard_service.py 2>&1 || true"], timeout=30)
        if out.strip():
            # if compilation error, it will show
            if "Traceback" in out or "Error" in out or "SyntaxError" in out:
                notes.append("Atenção: possível erro de Python/importe (py_compile):\n" + out.strip()[:800])
    else:
        notes.append("python3 não encontrado no host (checks de compile pulados).")

    return notes


def product_improvements() -> List[str]:
    return [
        "Monitoramento contínuo real: trocar o eixo de 'search_id' por 'app_id' (entidade estável) e criar histórico (mesmo que em SQLite por enquanto).",
        "Taxonomia fechada (PT-BR, snake_case) com validação: tags sempre dentro de um catálogo; max 3 tags por review; fallback 'outros'.",
        "Alertas vendáveis: detectar aumento de %negativo e spikes em tags críticas (login/pagamento/instabilidade) + bullets executivos no dashboard.",
    ]


def selling_points() -> List[str]:
    return [
        "Diagnóstico rápido de gargalos operacionais via voz do cliente (Play Store) com evidência (exemplos reais + métricas).",
        "Painel executivo: status/risco (0–100), tendência e top 3 dores/top 3 forças — pronto para slide de diretoria.",
        "Ciclo contínuo: acompanhar antes/depois de releases (regressões), priorizar backlog por impacto percebido pelo cliente.",
    ]


def objections_and_answers() -> List[str]:
    return [
        "Objeção: 'Isso é só sentimento genérico.' → Resposta: além do sentimento, entregamos intenção/tema + evidência e tendência por período.",
        "Objeção: 'E dados internos?' → Resposta: começamos com fontes públicas (zero integração) e evoluímos para tickets/CRM depois.",
        "Objeção: 'Qual ROI?' → Resposta: reduz incêndios e melhora priorização; medimos por queda de %negativo e redução de recorrência por tema.",
    ]


def backlog_suggestions() -> List[str]:
    # Notion-ready card titles (you can paste)
    return [
        "[P0] Dashboard: títulos humanos para insights (map tag → label PT-BR)",
        "[P0] Dashboard: incluir alerts[] (spike %negativo, tag crítica, tendência)",
        "[P1] Search: criar entidade 'monitor' por playstore_app_id (monitoramento contínuo)",
        "[P1] Taxonomia: catálogo fechado + validação no classify_text (max 3 tags)",
        "[P2] Observabilidade: logs estruturados + duration por etapa (coleta/classificação/dashboard)",
        "[P2] Venda: página 1-pager (problema → solução → demo → próximos passos)",
    ]


def subagent_split() -> List[str]:
    return [
        "Agente A (produto): definir taxonomia v1 e tags críticas por setor + copy do dashboard (títulos e bullets).",
        "Agente B (engenharia): implementar monitoramento contínuo (app_id estável + cron de coleta).",
        "Agente C (vendas): montar pitch de 60s + email/DM template + roteiro de reunião discovery.",
    ]


def main() -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    commits = git_recent_commits(8)
    changed = git_changed_files()
    health = repo_health_notes()

    lines: List[str] = []
    lines.append(f"🗓️ Daily Review — Reputation Intelligence ({now})")
    lines.append("")

    lines.append("1) Status técnico (últimos commits)")
    lines.append(commits)
    lines.append("")

    lines.append("2) Mudanças nas últimas 24h (arquivos)")
    lines.append(changed)
    lines.append("")

    lines.append("3) Qualidade/alertas rápidos")
    if health:
        lines.extend(f"- {n}" for n in health)
    else:
        lines.append("- OK")
    lines.append("")

    lines.append("4) Melhorias de produto (prioridade)")
    lines.extend(f"- {x}" for x in product_improvements())
    lines.append("")

    lines.append("5) Backlog sugerido (para Notion)")
    lines.extend(f"- {x}" for x in backlog_suggestions())
    lines.append("")

    lines.append("6) Quebra para sub-agentes")
    lines.extend(f"- {x}" for x in subagent_split())
    lines.append("")

    lines.append("7) Venda (enterprise): argumentos")
    lines.extend(f"- {x}" for x in selling_points())
    lines.append("")

    lines.append("8) Objeções comuns + respostas")
    lines.extend(f"- {x}" for x in objections_and_answers())

    print("\n".join(lines).strip())


if __name__ == "__main__":
    main()
