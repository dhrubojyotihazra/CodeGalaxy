"""
CodeGalaxy Backend - Configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # GitHub
    github_token: str = ""

    # Embedding model: "local" or "openrouter"
    embedding_model: str = "local"
    groq_api_key: Optional[str] = None
    groq_model: str = "qwen/qwen3.8-27b"
    openrouter_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/codegalaxy.db"

    # UMAP parameters
    umap_n_neighbors: int = 15
    umap_min_dist: float = 0.1
    umap_spread: float = 2.0

    # Supported file extensions
    supported_extensions: list[str] = [
        ".py", ".js", ".jsx", ".ts", ".tsx",
        ".java", ".go", ".rs", ".rb", ".cpp",
        ".c", ".h", ".hpp", ".cs", ".php",
    ]

    # Coordinate bounds for 3D space
    coord_range: float = 50.0

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
