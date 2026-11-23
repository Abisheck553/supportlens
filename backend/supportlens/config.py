from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "sqlite:///./data/supportlens.db"
    answer_provider: Literal["extractive", "ollama"] = "extractive"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:4b-instruct"
    ollama_timeout: float = 120
    ollama_context_length: int = 4096
    ollama_max_tokens: int = 512
    enable_semantic: bool = False
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    seed_demo: bool = True
