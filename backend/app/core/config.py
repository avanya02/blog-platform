from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Blog Platform API"
    environment: str = "development"
    database_url: str = "sqlite:///./blog_platform.db"
    cors_origins: str = "http://localhost:5173"
    secret_key: str = "development-only-change-me"
    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
