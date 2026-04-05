from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional


class TagDef(BaseModel):
    id: str = Field(..., description="snake_case, sem acento")
    label: str = Field(..., description="PT-BR, humano")
    aliases: List[str] = Field(default_factory=list)


class CompanyProfile(BaseModel):
    company_name: str
    sector: Optional[str] = None
    size: Optional[str] = None  # micro|pequena|media|grande|enterprise|unknown
    products: List[TagDef] = Field(default_factory=list, description="0-20")
    intents: List[TagDef] = Field(default_factory=list, description="0-20")
    notes: Optional[str] = None
