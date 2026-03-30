from typing import Any, Dict


class InMemoryStore:
    """Armazenamento simples para MVP (substituir por DB depois)."""

    def __init__(self) -> None:
        self.searches: Dict[str, Dict[str, Any]] = {}
        self.reviews: Dict[str, Dict[str, Any]] = {}


store = InMemoryStore()
