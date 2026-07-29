from functools import lru_cache
from pathlib import Path
from typing import Self

from dotenv import load_dotenv
from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AGI_", env_file=".env", extra="ignore")

    environment: str = "development"
    database_url: str = "sqlite:///./data/agi.db"
    bootstrap_token: str = "local-bootstrap-token"
    bootstrap_token_file: Path | None = None
    session_secret: str = "development-only-session-secret-change-me"
    session_secret_file: Path | None = None
    master_key: str = "development-only-master-key"
    master_key_file: Path | None = None
    demo_no_auth: bool = True
    knowledge_root: Path = Field(default=Path("knowledge"))
    ollama_base_url: str = "http://localhost:11434/v1"
    model_profile: str = "local-balanced"
    qmd_url: str | None = None
    cloud_models_enabled: bool = False
    cloud_provider: str | None = None
    cloud_api_key: SecretStr | None = None
    cloud_api_key_file: Path | None = None
    cloud_model: str | None = None
    otlp_endpoint: str | None = None
    static_dir: Path = Path("apps/web/dist")

    @model_validator(mode="after")
    def validate_security_profile(self) -> Self:
        for value_field, file_field, label in (
            ("bootstrap_token", "bootstrap_token_file", "Bootstrap token"),
            ("session_secret", "session_secret_file", "Session secret"),
            ("master_key", "master_key_file", "Master key"),
        ):
            secret_path = getattr(self, file_field)
            if secret_path is not None:
                try:
                    secret = secret_path.read_text(encoding="utf-8").strip()
                except OSError as error:
                    raise ValueError(f"{label} secret file cannot be read") from error
                if not secret:
                    raise ValueError(f"{label} secret file is empty")
                setattr(self, value_field, secret)
        if self.cloud_api_key_file is not None and str(self.cloud_api_key_file) not in ("", "."):
            if self.cloud_api_key_file.is_dir():
                raise ValueError("Cloud API key secret file is a directory")
            try:
                secret = self.cloud_api_key_file.read_text(encoding="utf-8").strip()
            except OSError as error:
                raise ValueError("Cloud API key secret file cannot be read") from error
            if secret:
                self.cloud_api_key = SecretStr(secret)
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
            if self.cloud_models_enabled and self.cloud_api_key_file is None:
                raise ValueError("Production cloud API keys must be mounted from a secret file")
        return self

    @property
    def company_bundle(self) -> Path:
        root = self.knowledge_root
        candidate = root / "bundles" / "company"
        return candidate if root.name != "company" else root

    @property
    def raw_root(self) -> Path:
        return self.knowledge_root / "raw"

    @property
    def candidates_root(self) -> Path:
        return self.knowledge_root / "candidates"

    @property
    def uploads_root(self) -> Path:
        return self.knowledge_root / "uploads"


@lru_cache
def get_settings() -> Settings:
    return Settings()
