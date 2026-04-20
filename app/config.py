from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")  # replaces class Config

    app_name: str = "Banking API"
    app_version: str = "1.0.0"
    debug: bool = False

    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Database
    database_url: str

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    


@lru_cache()
def get_settings() -> Settings:
    return Settings()