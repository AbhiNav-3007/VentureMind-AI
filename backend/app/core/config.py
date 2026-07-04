"""
VentureMind AI — Core Configuration
Loads all settings from environment variables with sensible defaults.

IBM Granite model IDs available on watsonx.ai Lite plan (free tier):
  ibm/granite-3-8b-instruct   — best balance of quality + speed (recommended)
  ibm/granite-3-2b-instruct   — fastest, lower quality
  ibm/granite-13b-instruct-v2 — older generation, also available

Watson Discovery has been removed — no Lite/free plan available.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "VentureMind AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # ── PostgreSQL Database ───────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/venturemind"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # ── ChromaDB (Vector Store) ───────────────────────────────────────────────
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    CHROMA_COLLECTION_NAME: str = "venturemind_rag"

    # ── IBM watsonx.ai ────────────────────────────────────────────────────────
    # Lite-plan available Granite models:
    #   ibm/granite-3-8b-instruct  (recommended — best quality on Lite)
    #   ibm/granite-3-2b-instruct  (fastest)
    #   ibm/granite-13b-instruct-v2 (older generation)
    IBM_WATSONX_URL: str = "https://us-south.ml.cloud.ibm.com"
    IBM_WATSONX_API_KEY: str = ""
    IBM_WATSONX_PROJECT_ID: str = ""
    IBM_GRANITE_MODEL_ID: str = "ibm/granite-4-h-small"
    IBM_GRANITE_MAX_NEW_TOKENS: int = 2048
    IBM_GRANITE_TEMPERATURE: float = 0.7
    IBM_GRANITE_TOP_P: float = 0.9

    # ── IBM Cloud Object Storage (optional) ──────────────────────────────────
    IBM_COS_API_KEY: str = ""
    IBM_COS_INSTANCE_CRN: str = ""
    IBM_COS_ENDPOINT: str = "https://s3.us-south.cloud-object-storage.appdomain.cloud"
    IBM_COS_BUCKET_NAME: str = "venturemind-reports"
    IBM_COS_AUTH_ENDPOINT: str = "https://iam.cloud.ibm.com/identity/token"

    # ── IBM Orchestrate (optional) ────────────────────────────────────────────
    IBM_ORCHESTRATE_URL: str = ""
    IBM_ORCHESTRATE_API_KEY: str = ""

    # ── Report Generation ─────────────────────────────────────────────────────
    REPORT_OUTPUT_DIR: str = "/tmp/venturemind_reports"
    PDF_FONT_PATH: str = ""

    # ── Agent Timeouts (seconds) ──────────────────────────────────────────────
    AGENT_TIMEOUT_SECONDS: int = 300
    ORCHESTRATOR_TIMEOUT_SECONDS: int = 600

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
