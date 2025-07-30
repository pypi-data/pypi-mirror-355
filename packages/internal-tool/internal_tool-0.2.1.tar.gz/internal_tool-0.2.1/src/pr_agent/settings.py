# pr_agent/settings.py
import os
from typing import ClassVar
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):

    METADATA_DIR: Path = Field(
        default=BASE_DIR / "internal-processed-docs" / "metadata",
        description="Where per-doc metadata JSONs live",
    )
    
    RAW_DIR: Path = Field(
        default=BASE_DIR / "internal-processed-docs" / "raw",
        description="Where raw text JSONs are written",
    )

    EMBEDDINGS_DIR: Path = Field(
        default=BASE_DIR / "internal-processed-docs" / "embeddings",
        description="Where .npy embeddings are stored",
    )

    # ─── Download directory ────────────────────────────────────────────────
    DOWNLOAD_DIR: Path = Field(
        default=Path.home() / "Downloads",
        env="DOWNLOAD_DIR",
        description="Default directory where downloaded files are saved"
    )

    # ─── Google Drive settings ──────────────────────────────────────────────
    GDRIVE_CRED_FILE: Path = Field(
        ...,
        description="Path to your Google service-account JSON",
    )
    GDRIVE_FOLDER_ID: str = Field(
        ...,
        description="Root folder ID in Google Drive to crawl",
    )

    # ─── Notion settings ────────────────────────────────────────────────────
    NOTION_TOKEN: str = Field(
        ...,
        description="Integration token for your Notion workspace",
    )
    NOTION_ROOT_PAGE_ID: str = Field(
        ...,
        description="Root page ID in Notion to crawl",
    )

    # ─── Pinecone settings ────────────────────────────────────────────────────
    PINECONE_API_KEY: str = Field(
        ..., env="PINECONE_API_KEY",
        description="Your Pinecone API key"
    )

    PINECONE_ENV: str = Field(
        ..., env="PINECONE_ENV",
        description="Your Pinecone environment"
    )

    PINECONE_INDEX: str = Field(
        "halo-embeds", env="PINECONE_INDEX",
        description="Name of your Pinecone index"
    )

# ─── Gemini (Google Generative AI) settings ─────────────────────────────
    GEMINI_API_KEY: str = Field(
        ..., env="GEMINI_API_KEY",
        description="Your Google Generative AI API key for Gemini models"
    )
    GEMINI_MODEL:   str = Field(
        "gemini-1.5-flash-latest", env="GEMINI_MODEL",
        description="Name of the Gemini model to use"
    )

    # ─── General settings ────────────────────────────────────────────────────
    GDRIVE_SCOPES: ClassVar[list[str]] = ["https://www.googleapis.com/auth/drive.readonly"]
    EMBEDDING_MODEL: ClassVar[list[str]] = "all-MiniLM-L6-v2"
    # OLLAMA_BASE_URL: ClassVar[list[str]] = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    # OLLAMA_MODEL_SHORT: ClassVar[list[str]] = os.getenv("OLLAMA_MODEL_SHORT", "mistral")
    EMBED_TOKEN_MODEL: ClassVar[list[str]] = os.getenv("EMBED_TOKEN_MODEL", "text-embedding-ada-002")
    TOKEN_LIMIT: ClassVar[list[str]] = int(os.getenv("TOKEN_LIMIT", "550"))
    TOP_TOPIC_COUNT: ClassVar[list[str]] = 3


    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# instantiate once for import
settings = Settings()
