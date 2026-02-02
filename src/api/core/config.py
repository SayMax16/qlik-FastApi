"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Settings
    APP_NAME: str = Field(default="Qlik Sense REST API", description="Application name")
    APP_VERSION: str = Field(default="0.1.0", description="Application version")
    DEBUG: bool = Field(default=False, description="Debug mode")
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # API Settings
    API_V1_PREFIX: str = Field(default="/api/v1", description="API v1 prefix")
    API_KEY: str = Field(..., description="API key for authentication")
    ALLOWED_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="CORS allowed origins",
    )

    # Qlik Sense Configuration
    QLIK_SENSE_HOST: str = Field(..., description="Qlik Sense server hostname")
    QLIK_SENSE_PORT: int = Field(default=4747, description="Qlik Sense server port")
    QLIK_ENGINE_PORT: int = Field(default=4747, description="Qlik Engine API port")
    QLIK_REPOSITORY_PORT: int = Field(default=4242, description="Qlik Repository API port")

    # Qlik Authentication
    QLIK_USER_DIRECTORY: str = Field(..., description="Qlik user directory (domain)")
    QLIK_USER_ID: str = Field(..., description="Qlik user ID")

    # Certificate Paths
    QLIK_CERT_PATH: str = Field(default="certs/client.pem", description="Client certificate path")
    QLIK_KEY_PATH: str = Field(
        default="certs/client_key.pem", description="Client key path"
    )
    QLIK_ROOT_CERT_PATH: str = Field(default="certs/root.pem", description="Root CA path")

    # Connection Settings
    QLIK_VERIFY_SSL: bool = Field(default=True, description="Verify SSL certificates")
    QLIK_CONNECTION_TIMEOUT: int = Field(default=30, description="Connection timeout in seconds")
    QLIK_REQUEST_TIMEOUT: int = Field(default=60, description="Request timeout in seconds")

    # WebSocket Settings
    QLIK_WS_TIMEOUT: int = Field(default=300, description="WebSocket timeout in seconds")
    QLIK_WS_PING_INTERVAL: int = Field(
        default=30, description="WebSocket ping interval in seconds"
    )

    # API Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=False, description="Enable rate limiting")
    RATE_LIMIT_REQUESTS: int = Field(
        default=100, description="Max requests per period"
    )
    RATE_LIMIT_PERIOD: int = Field(default=60, description="Rate limit period in seconds")

    # CORS Settings
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="Allow credentials")
    CORS_ALLOW_METHODS: list[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="Allowed HTTP methods",
    )
    CORS_ALLOW_HEADERS: list[str] = Field(default=["*"], description="Allowed headers")

    # App and Table Mappings
    APP_MAPPINGS_JSON: str = Field(default='{}', description="JSON mapping of app names to IDs")
    DEFAULT_TABLE_MAPPINGS_JSON: str = Field(default='{}', description="JSON mapping of app names to default table IDs")

    @field_validator("ALLOWED_ORIGINS", "CORS_ALLOW_METHODS", "CORS_ALLOW_HEADERS", mode="before")
    @classmethod
    def parse_list_from_string(cls, v: Any) -> list[str]:
        """Parse list from string or return as-is if already a list."""
        if isinstance(v, str):
            # Handle string representation of list like "['item1', 'item2']"
            import ast
            try:
                return ast.literal_eval(v)
            except (ValueError, SyntaxError):
                # Handle comma-separated string
                return [item.strip() for item in v.split(",")]
        return v

    @property
    def qlik_engine_url(self) -> str:
        """Get the Qlik Engine API WebSocket URL."""
        return f"wss://{self.QLIK_SENSE_HOST}:{self.QLIK_ENGINE_PORT}/app"

    @property
    def qlik_repository_url(self) -> str:
        """Get the Qlik Repository API base URL."""
        return f"https://{self.QLIK_SENSE_HOST}:{self.QLIK_REPOSITORY_PORT}"

    @property
    def cert_files_exist(self) -> bool:
        """Check if all required certificate files exist."""
        project_root = Path(__file__).parent.parent.parent.parent
        cert_path = project_root / self.QLIK_CERT_PATH
        key_path = project_root / self.QLIK_KEY_PATH
        root_path = project_root / self.QLIK_ROOT_CERT_PATH
        return cert_path.exists() and key_path.exists() and root_path.exists()

    def get_cert_paths(self) -> tuple[Path, Path, Path]:
        """Get absolute paths to certificate files."""
        project_root = Path(__file__).parent.parent.parent.parent
        return (
            project_root / self.QLIK_CERT_PATH,
            project_root / self.QLIK_KEY_PATH,
            project_root / self.QLIK_ROOT_CERT_PATH,
        )

    @property
    def app_mappings(self) -> dict[str, str]:
        """Get app name to ID mappings."""
        import json
        try:
            return json.loads(self.APP_MAPPINGS_JSON)
        except (json.JSONDecodeError, ValueError):
            return {}

    @property
    def default_table_mappings(self) -> dict[str, str]:
        """Get app name to default table ID mappings."""
        import json
        try:
            return json.loads(self.DEFAULT_TABLE_MAPPINGS_JSON)
        except (json.JSONDecodeError, ValueError):
            return {}

    def get_app_id(self, app_name: str) -> str | None:
        """Get app ID by name."""
        return self.app_mappings.get(app_name)

    def get_default_table_id(self, app_name: str) -> str | None:
        """Get default table ID for an app."""
        return self.default_table_mappings.get(app_name)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
