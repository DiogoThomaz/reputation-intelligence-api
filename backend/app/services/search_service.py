from uuid import uuid4

from app.repositories.inmemory import store


def create_search(company_name: str) -> str:
    sid = str(uuid4())
    store.searches[sid] = {"status": "processing", "company_name": company_name}
    return sid


def get_search(search_id: str):
    return store.searches.get(search_id)
