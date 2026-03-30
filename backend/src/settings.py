from pydantic import BaseModel


class Settings(BaseModel):
    database_url: str = "sqlite:///./app.db"
    ollama_base_url: str = "http://187.127.3.91:32768"
    ollama_model: str = "qwen2.5:3b-instruct"


settings = Settings()
