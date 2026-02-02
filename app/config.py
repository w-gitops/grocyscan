"""Application configuration using Pydantic Settings."""

import tomllib
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _get_version() -> str:
    """Read version from pyproject.toml (single source of truth)."""
    try:
        pyproject = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
        return data["project"]["version"]
    except Exception:
        return "0.0.0-dev"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Core
    grocyscan_version: str = _get_version()
    grocyscan_env: Literal["development", "staging", "production"] = "development"
    grocyscan_debug: bool = False
    grocyscan_host: str = "0.0.0.0"
    grocyscan_port: int = 3334
    grocyscan_secret_key: SecretStr = Field(
        default=SecretStr("change-me-to-a-secure-32-character-secret"),
        description="Secret key for session encryption (32+ characters)",
    )

    # API Documentation
    docs_enabled: bool = True
    openapi_url: str = "/api/v1/openapi.json"

    # Database
    database_url: SecretStr = Field(
        default=SecretStr("postgresql+asyncpg://grocyscan:grocyscan@localhost:5432/grocyscan"),
        description="PostgreSQL connection URL",
    )
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_echo: bool = False

    # Redis Cache
    redis_url: str = "redis://localhost:6379/0"
    redis_password: SecretStr = SecretStr("")
    cache_ttl_days: int = 30

    # Grocy Integration
    grocy_api_url: str = "http://localhost:9283"
    grocy_api_key: SecretStr = SecretStr("")
    grocy_web_url: str = "http://localhost:9283"
    grocy_timeout_seconds: int = 30

    # LLM Configuration
    llm_provider_preset: Literal["openai", "anthropic", "ollama", "generic"] = "ollama"
    llm_api_url: str = "http://localhost:11434/v1"
    llm_api_key: SecretStr = SecretStr("")
    llm_model: str = "llama3.1:8b"
    llm_timeout_seconds: int = 60
    llm_max_retries: int = 3

    # Lookup Providers
    lookup_strategy: Literal["sequential", "parallel"] = "sequential"
    lookup_provider_order: str = "openfoodfacts,goupc,upcitemdb,brave,federation"
    lookup_timeout_seconds: int = 10

    openfoodfacts_enabled: bool = True
    openfoodfacts_user_agent: str = "GrocyScan/1.0"

    goupc_enabled: bool = False
    goupc_api_key: SecretStr = SecretStr("")

    upcitemdb_enabled: bool = False
    upcitemdb_api_key: SecretStr = SecretStr("")

    brave_enabled: bool = False
    brave_api_key: SecretStr = SecretStr("")
    brave_use_as_fallback: bool = True

    federation_enabled: bool = False
    federation_url: str = ""

    # Scanning Behavior
    auto_add_enabled: bool = False
    fuzzy_match_threshold: float = 0.9
    default_quantity_unit: str = "pieces"
    kiosk_mode_enabled: bool = False

    # Authentication
    auth_enabled: bool = True
    auth_username: str = "admin"
    auth_password_hash: SecretStr = SecretStr("")
    session_timeout_hours: int = 24
    session_absolute_timeout_days: int = 7

    external_api_enabled: bool = True
    external_api_rate_limit: int = 100

    # MCP Server
    mcp_enabled: bool = False
    mcp_port: int = 3335
    mcp_transport: str = "streamable-http"
    mcp_require_api_key: bool = True

    # Observability
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: Literal["json", "console"] = "json"
    log_file: str = ""

    otel_enabled: bool = False
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_exporter_otlp_insecure: bool = True
    otel_service_name: str = "grocyscan"

    metrics_enabled: bool = True
    metrics_port: int = 3334

    @field_validator("lookup_provider_order")
    @classmethod
    def validate_provider_order(cls, v: str) -> str:
        """Validate and normalize provider order."""
        valid_providers = {"openfoodfacts", "goupc", "upcitemdb", "brave", "federation"}
        providers = [p.strip().lower() for p in v.split(",") if p.strip()]
        for provider in providers:
            if provider not in valid_providers:
                raise ValueError(f"Invalid provider: {provider}")
        return ",".join(providers)

    @property
    def provider_list(self) -> list[str]:
        """Get lookup providers as a list."""
        return [p.strip() for p in self.lookup_provider_order.split(",") if p.strip()]

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.grocyscan_env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.grocyscan_env == "production"


# Global settings instance
settings = Settings()
