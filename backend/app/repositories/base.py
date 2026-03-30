from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.models import Search


class SearchRepository(ABC):
    @abstractmethod
    def create(self, *, search: Search) -> None:
        raise NotImplementedError

    @abstractmethod
    def get(self, *, search_id: str) -> Optional[Search]:
        raise NotImplementedError
