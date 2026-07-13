from functools import lru_cache
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, SecretStr, model_validator
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

    @model_validator(mode="after")
    def validate_security_profile(self) -> Self:
        if self.cloud_models_enabled and (
            self.cloud_provider is None or self.cloud_api_key is None
        ):
            raise ValueError("Cloud models require an explicit provider and API key")
        if self.environment.lower() == "production":
            insecure_values = {
                "local-bootstrap-token",
                "replace-this-one-time-token",
                "development-only-session-secret-change-me",
                "replace-with-at-least-32-random-characters",
                "development-only-master-key",
                "replace-with-a-docker-secret-in-production",
            }
            if self.demo_no_auth:
                raise ValueError("AGI_DEMO_NO_AUTH cannot be enabled in production")
            if self.bootstrap_token in insecure_values or len(self.bootstrap_token) < 24:
                raise ValueError("Production bootstrap token must be a non-default secret")
            if self.session_secret in insecure_values or len(self.session_secret) < 32:
                raise ValueError("Production session secret must be a non-default secret")
            if self.master_key in insecure_values or len(self.master_key) < 32:
                raise ValueError("Production master key must be a non-default secret")
        return self

    @property
    def company_bundle(self) -> Path:
        root = self.knowledge_root
        candidate = root / "bundles" / "company"
        return candidate if root.name != "company" else root


@lru_cache
def get_settings() -> Settings:
    return Settings()
