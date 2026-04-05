from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    search_id: Mapped[str] = mapped_column(String, index=True)
    source: Mapped[str] = mapped_column(String)
    rating: Mapped[int] = mapped_column(Integer)
    date: Mapped[str] = mapped_column(String)
    author: Mapped[str] = mapped_column(String, nullable=True)
    text: Mapped[str] = mapped_column(Text)

    sentiment: Mapped[str] = mapped_column(String, nullable=True)
    intent_tags: Mapped[str] = mapped_column(Text, nullable=True)
    product_tags: Mapped[str] = mapped_column(Text, nullable=True)
    ai_model: Mapped[str] = mapped_column(String, nullable=True)
