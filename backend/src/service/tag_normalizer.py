import re
import unicodedata
from typing import Iterable, List


def to_snake_case_pt(s: str) -> str:
    s = (s or "").strip().lower()
    # remove accents
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    # replace non alnum with underscore
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = s.strip("_")
    # collapse
    s = re.sub(r"_+", "_", s)
    return s


def normalize_tag_list(tags: Iterable[str], max_items: int = 4) -> List[str]:
    out: List[str] = []
    seen = set()
    for t in tags or []:
        v = to_snake_case_pt(str(t))
        if not v:
            continue
        if v in seen:
            continue
        seen.add(v)
        out.append(v)
        if len(out) >= max_items:
            break
    return out
