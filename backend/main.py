"""DEPRECATED.

Use `uvicorn app.main:app`.
Este arquivo existe apenas para não quebrar referências antigas.
"""

from app.main import app  # noqa: F401
