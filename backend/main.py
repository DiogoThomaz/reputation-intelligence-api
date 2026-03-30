from fastapi import FastAPI, Query, Path
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import uuid4

app = FastAPI(title="Reputation Intelligence API")

# Mock databases (em memória por enquanto)
SEARCHES = {}
REVIEWS = {}

# ------ MODELS ------
class SearchRequest(BaseModel):
    company_name: str

class SearchResponse(BaseModel):
    search_id: str
    status: str

class ReviewItem(BaseModel):
    id: str
    company_name: str
    source: str
    sentiment: str
    intent_tags: List[str]
    comment_text: str
    rating: Optional[int]
    date: str

class SearchResultResponse(BaseModel):
    search_id: str
    status: str
    company_name: str
    summary: Dict[str, Any]
    items: List[ReviewItem]

class DashboardResponse(BaseModel):
    search_id: str
    sentiment_distribution: Dict[str, int]
    top_intent_tags: List[str]
    by_source: Dict[str, int]

# ------ ROUTES ------
@app.post("/search", response_model=SearchResponse)
def create_search(req: SearchRequest):
    # Mock: inicia busca, armazena status e devolve search_id
    sid = str(uuid4())
    SEARCHES[sid] = {
        "status": "processing",
        "company_name": req.company_name
    }
    # Aqui inicia pipeline async (mock por enquanto)
    return {"search_id": sid, "status": "processing"}

@app.get("/search/{search_id}", response_model=SearchResultResponse)
def get_search(search_id: str = Path(...)):
    # Mock output
    data = SEARCHES.get(search_id)
    if not data:
        return {"search_id": search_id, "status": "not_found", "company_name": "", "summary": {}, "items": []}
    # Preenche resultado fake caso já "finalizado"
    return {
        "search_id": search_id,
        "status": data.get("status", "processing"),
        "company_name": data["company_name"],
        "summary": {"total_items": 0, "by_source": {}, "by_sentiment": {}},
        "items": []
    }

@app.get("/reviews", response_model=List[ReviewItem])
def list_reviews(
    search_id: str = Query(...),
    source: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    tag: Optional[str] = Query(None)
):
    # Mock - vazio
    return []

@app.get("/dashboard/{search_id}", response_model=DashboardResponse)
def get_dashboard(search_id: str = Path(...)):
    # Mock - vazio
    return {
        "search_id": search_id,
        "sentiment_distribution": {},
        "top_intent_tags": [],
        "by_source": {}
    }

@app.get("/health")
def health():
    return {"status": "ok"}
