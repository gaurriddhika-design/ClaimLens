from functools import cached_property
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed settings. Never return secret values from API routes."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    llm_provider: str = ""
    llm_model: str = ""
    llm_api_key: str = ""
    llm_base_url: str = ""
    search_provider: str = ""
    search_api_key: str = ""
    tavily_api_key: str = ""
    database_url: str = "sqlite+aiosqlite:///./claimlens.db"
    frontend_api_url: str = "http://localhost:3000"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    max_upload_mb: int = 10
    max_pdf_pages: int = 50
    max_claims: int = 20
    request_timeout_seconds: float = 15.0
    max_text_chars: int = 100_000
    max_url_response_bytes: int = 2_000_000

    @cached_property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def configured_search_api_key(self) -> str:
        """Prefer the configured search key and retain Tavily's legacy env name."""
        return self.search_api_key.strip() or self.tavily_api_key.strip()

    @property
    def search_provider_is_configured(self) -> bool:
        provider = self.search_provider.strip().lower()
        if not provider and self.tavily_api_key.strip():
            provider = "tavily"
        return provider == "tavily" and bool(self.configured_search_api_key)


settings = Settings()
