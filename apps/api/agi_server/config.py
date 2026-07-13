from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AGI_", env_file=".env", extra="ignore")

    environment: str = "development"
    database_url: str = "sqlite:///./data/agi.db"
    bootstrap_token: str = "local-bootstrap-token"
    session_secret: str = "development-only-session-secret-change-me"
    master_key: str = "development-only-master-key"
    demo_no_auth: bool = True
    enable_dbos: bool = False
    knowledge_root: Path = Field(default=Path("knowledge"))
    ollama_base_url: str = "http://localhost:11434/v1"
    model_profile: str = "local-balanced"
    qmd_url: str | None = None
    cloud_models_enabled: bool = False
    cloud_provider: Literal["groq", "mistral"] | None = None
    cloud_api_key: SecretStr | None = None
    cloud_model: str | None = None
    static_dir: Path = Path("apps/web/dist")

    @property
    def company_bundle(self) -> Path:
        root = self.knowledge_root
        candidate = root / "bundles" / "company"
        return candidate if root.name != "company" else root


@lru_cache
def get_settings() -> Settings:
    return Settings()
