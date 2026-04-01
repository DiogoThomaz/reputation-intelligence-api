import os

from pydantic import BaseModel


class Settings(BaseModel):
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")

    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://187.127.3.91:32768")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:3b-instruct")

    # Batch/chunk config
    ollama_batch_max_items: int = int(os.getenv("OLLAMA_BATCH_MAX_ITEMS", "10"))
    ollama_batch_max_chars: int = int(os.getenv("OLLAMA_BATCH_MAX_CHARS", "1000"))
