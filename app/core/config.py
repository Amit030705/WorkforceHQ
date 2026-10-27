from functools import lru_cache

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Employee Management System"
    environment: str = "development"
    database_url: PostgresDsn
    test_database_url: PostgresDsn | None = None
    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=30, gt=0, le=1440)
    frontend_origin: str = "http://127.0.0.1:8000"
    cookie_secure: bool = False

    @field_validator("jwt_algorithm")
    @classmethod
    def only_allow_hmac_sha256(cls, value: str) -> str:
        if value != "HS256":
            raise ValueError("Only the HS256 JWT algorithm is supported.")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()

