from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment or .env.

    LLM backend:
      MOCK_LLM=true  → deterministic mock (safe for demos, no network)
      MOCK_LLM=false → standard OpenAI API (requires OPENAI_API_KEY)
    """

    # ── Storage ──────────────────────────────────────────────────────────────
    storage_backend: str = "excel"
    excel_store_path: str = "data/supervisor_control_tower.xlsx"
    database_url: str = "postgresql+psycopg2://supervisor:supervisor@localhost:5432/supervisor_control_tower"

    # ── LLM — OpenAI ─────────────────────────────────────────────────────────
    openai_api_key: str | None = None
    llm_model: str = "gpt-4o-mini"
    mock_llm: bool = True
    llm_timeout_seconds: int = Field(default=30, ge=1, le=120)

    # ── Auth ──────────────────────────────────────────────────────────────────
    auth_enabled: bool = True
    demo_auth: bool = True
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str = "http://localhost:8501"

    # ── App ───────────────────────────────────────────────────────────────────
    app_env: str = "POC"
    log_level: str = "INFO"

    high_confidence_threshold: float = Field(default=0.80, ge=0, le=1)
    minimum_confidence_threshold: float = Field(default=0.60, ge=0, le=1)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


def _coerce_secret(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _load_streamlit_secrets_into_environment() -> None:
    """Allows the app to run on Streamlit without changing application code.

    This function is intentionally silent outside Streamlit and never overwrites an
    explicit environment variable. Scripts such as init_db.py and seed_data.py still
    work with .env or shell-provided environment variables.
    """

    try:
        import streamlit as st  # type: ignore

        secrets = getattr(st, "secrets", {})
        for field_name in Settings.model_fields:
            env_name = field_name.upper()
            if os.getenv(env_name) is not None:
                continue
            if env_name in secrets:
                os.environ[env_name] = _coerce_secret(secrets[env_name])
            elif field_name in secrets:
                os.environ[env_name] = _coerce_secret(secrets[field_name])
    except Exception:
        return


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    _load_streamlit_secrets_into_environment()
    return Settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()
