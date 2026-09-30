import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

# Paths
BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent

class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "College AI Knowledge Base"
    API_V1_STR: str = "/api"
    DEBUG: bool = False

    # Google Gemini
    GEMINI_API_KEY: str = ""
    LLM_MODEL: str = "gemini-3.6-flash"
    # EMBEDDING_MODEL can be:
    # - "models/text-embedding-004" (Google Gemini - may not be available)
    # - "local" (use Chroma's local ONNX all-MiniLM-L6-v2, 384-dimensional)
    EMBEDDING_MODEL: str = "local"

    # Database
    DATABASE_URL: str = f"sqlite:///{BACKEND_DIR / 'college_ai.db'}"

    # ChromaDB Vector Store
    CHROMA_PERSIST_DIR: str = str(BACKEND_DIR / "data" / "chroma_db")
    CHROMA_COLLECTION_NAME: str = "college_knowledge_base"

    # Knowledge Base Path (Points to workspace root where the 5 document folders live)
    DOCUMENTS_ROOT_DIR: str = str(ROOT_DIR)

    # RAG Settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RESULTS: int = 6

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
