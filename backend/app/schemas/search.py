from pydantic import BaseModel


class SearchCreateRequest(BaseModel):
    company_name: str


class SearchCreateResponse(BaseModel):
    search_id: str
    status: str
