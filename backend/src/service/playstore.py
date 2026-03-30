from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Optional

from google_play_scraper import Sort, reviews


@dataclass(frozen=True)
class PlayStoreReview:
    source: str
    app_id: str
    rating: int
    date: str
    author: Optional[str]
    text: str


def search_playstore(
    app_id: str,
    *,
    max_reviews: int = 200,
    lang: str = "pt",
    country: str = "br",
) -> Iterator[PlayStoreReview]:
    """Busca reviews da Play Store via `google-play-scraper`.

    - `app_id`: ex: "com.nu.production"
    - Retorna `yield` incremental.

    Observação: essa lib não usa Playwright; é mais estável e simples para MVP.
    """

    remaining = max_reviews
    continuation_token = None

    while remaining > 0:
        batch_size = min(200, remaining)

        result, continuation_token = reviews(
            app_id,
            lang=lang,
            country=country,
            sort=Sort.NEWEST,
            count=batch_size,
            continuation_token=continuation_token,
        )

        if not result:
            break

        for r in result:
            # a lib retorna datetime em 'at'
            at = r.get("at")
            date = at.date().isoformat() if hasattr(at, "date") else str(at or "")

            print ("comment", r.get("content") or "")
            yield PlayStoreReview(
                source="play_store",
                app_id=app_id,
                rating=int(r.get("score") or 0),
                date=date,
                author=r.get("userName"),
                text=(r.get("content") or "").strip(),
            )

        remaining -= len(result)

        if not continuation_token:
            break
