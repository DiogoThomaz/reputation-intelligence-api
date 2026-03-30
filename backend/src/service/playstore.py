from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Optional
import random
import time

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError


PLAYSTORE_URL = "https://play.google.com/store/apps/details"

# Lista curta (boa o suficiente p/ MVP). Podemos ampliar depois.
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]


@dataclass(frozen=True)
class PlayStoreReview:
    source: str
    app_id: str
    rating: int
    date: str
    author: Optional[str]
    text: str


def _jitter_sleep(a: float = 0.3, b: float = 1.2) -> None:
    time.sleep(random.uniform(a, b))


def search_playstore(
    app_id: str,
    *,
    max_reviews: int = 200,
    hl: str = "pt_BR",
    gl: str = "BR",
    headless: bool = True,
) -> Iterator[PlayStoreReview]:
    """Coleta reviews do Play Store por app_id e faz yield incremental.

    Observação: scraping sujeito a mudanças de layout/anti-bot.
    """

    ua = random.choice(USER_AGENTS)
    viewport = {"width": random.choice([1280, 1366, 1440, 1536]), "height": random.choice([720, 768, 900])}

    url = f"{PLAYSTORE_URL}?id={app_id}&hl={hl}&gl={gl}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            user_agent=ua,
            viewport=viewport,
            locale=hl.replace("_", "-"),
            timezone_id="America/Sao_Paulo",
        )

        # bloqueia só recursos pesados (não bloqueia js/xhr)
        def _route(route):
            rtype = route.request.resource_type
            if rtype in ("image", "media", "font"):
                return route.abort()
            return route.continue_()

        context.route("**/*", _route)
        page = context.new_page()

        page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        _jitter_sleep()

        # tenta aceitar popup de cookies, se aparecer
        try:
            btn = page.get_by_role("button", name=lambda n: n and "Aceitar" in n)
            if btn.count() > 0:
                btn.first.click(timeout=2_000)
                _jitter_sleep()
        except Exception:
            pass

        # 1) Clica em "Ver todas as avaliações" (fluxo atual da Play Store)
        btn = None
        for label in ("Ver todas as avaliações", "See all reviews", "See all ratings"):
            loc = page.get_by_role("button", name=label)
            if loc.count() > 0:
                btn = loc.first
                break

        if not btn:
            loc = page.locator("text=Ver todas as avaliações")
            if loc.count() > 0:
                btn = loc.first

        if not btn:
            context.close()
            browser.close()
            return

        btn.scroll_into_view_if_needed(timeout=10_000)
        _jitter_sleep()
        btn.click(timeout=10_000)
        _jitter_sleep(0.8, 1.8)

        # 2) Coleta no overlay/dialog de avaliações e vai scrollando para carregar mais
        yielded = 0
        seen = set()

        dialog = page.get_by_role("dialog")
        container = dialog.first if dialog.count() > 0 else page

        for _ in range(120):
            cards = container.locator("css=div:has(span[aria-label*='star'])")
            count = cards.count()

            for i in range(count):
                if yielded >= max_reviews:
                    break

                card = cards.nth(i)
                try:
                    text_parts = card.locator("css=span").all_inner_texts()
                    full_text = "\n".join([t.strip() for t in text_parts if t.strip()])

                    rating_el = card.locator("css=span[aria-label*='star']").first
                    aria = rating_el.get_attribute("aria-label") or ""
                    rating = 0
                    for d in "54321":
                        if d in aria:
                            rating = int(d)
                            break

                    date = ""
                    date_loc = card.locator("css=span:has-text('202')")
                    if date_loc.count() > 0:
                        date = date_loc.first.inner_text().strip()

                    author = None
                    author_loc = card.locator("css=div[role='heading'], css=span[role='heading']")
                    if author_loc.count() > 0:
                        author = author_loc.first.inner_text().strip() or None

                    key = (full_text[:200], rating, date, author)
                    if key in seen:
                        continue
                    seen.add(key)

                    if full_text and rating:
                        yield PlayStoreReview(
                            source="play_store",
                            app_id=app_id,
                            rating=rating,
                            date=date,
                            author=author,
                            text=full_text,
                        )
                        yielded += 1

                except PWTimeoutError:
                    continue
                except Exception:
                    continue

            if yielded >= max_reviews:
                break

            container.mouse.wheel(0, random.randint(1600, 2600))
            _jitter_sleep(0.5, 1.7)

        context.close()
        browser.close()
