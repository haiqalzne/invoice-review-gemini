from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEPLOYMENT_NAME = "gpt-5.6-terra"


@dataclass(frozen=True)
class AppConfig:
    expected_customer_name: str = "Northstar Facilities B.V."
    expected_customer_vat_id: str = "NL00449544B01"
    database_url: str = "sqlite:///./data/documents.db"
    upload_dir: Path = Path("./data/uploads")
    max_upload_bytes: int = 4 * 1024 * 1024
    min_field_confidence: float = 0.80


APP_CONFIG = AppConfig()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    ai_provider: Literal["gemini", "azure"] = "gemini"
    gemini_api_key: SecretStr | None = None
    gemini_model: str = Field(default="gemini-3.5-flash-lite", pattern=r"^[a-zA-Z0-9._-]+$")
    gemini_max_output_tokens: int = Field(default=8192, ge=256, le=16384)
    gemini_timeout_seconds: int = Field(default=90, ge=5, le=180)
    azure_document_intelligence_endpoint: str = ""
    azure_document_intelligence_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_deployment: str = DEPLOYMENT_NAME
    azure_openai_api_key: str = ""
    allowed_origin: str = "http://localhost:5173"
    app_access_password: str | None = None
    app_session_secret: str | None = None
    frontend_dist_dir: Path | None = None

    @model_validator(mode="after")
    def validate_auth_settings(self) -> "Settings":
        if self.ai_provider == "gemini":
            key = self.gemini_api_key.get_secret_value().strip() if self.gemini_api_key else ""
            if not key or key.startswith("replace-"):
                raise ValueError("Set GEMINI_API_KEY in backend/.env using Google AI Studio.")
        else:
            for name in (
                "azure_document_intelligence_endpoint", "azure_document_intelligence_key",
                "azure_openai_endpoint", "azure_openai_api_key",
            ):
                value = getattr(self, name).strip()
                if not value or "your-resource" in value or value.startswith("replace-"):
                    raise ValueError(f"Set {name.upper()} before using AI_PROVIDER=azure.")
        password = (self.app_access_password or "").strip() or None
        secret = (self.app_session_secret or "").strip() or None
        if password and not secret:
            raise ValueError(
                "APP_SESSION_SECRET is required when APP_ACCESS_PASSWORD is set"
            )
        self.app_access_password = password
        self.app_session_secret = secret
        return self

    @property
    def auth_enabled(self) -> bool:
        return self.app_access_password is not None

    def resolve_frontend_dist(self) -> Path | None:
        if self.frontend_dist_dir is not None:
            path = self.frontend_dist_dir
            return path if path.is_dir() else None
        for candidate in (
            BACKEND_ROOT.parent / "frontend" / "dist",
            Path("/app/frontend/dist"),
        ):
            if candidate.is_dir():
                return candidate
        return None


@lru_cache
def get_settings() -> Settings:
    return Settings()
