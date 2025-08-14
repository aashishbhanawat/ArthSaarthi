import os
from typing import Optional

from pydantic import validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SECRET_KEY: str = "a_super_secret_key_that_should_be_changed"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Default admin user
    ADMIN_USERNAME: str = "admin"
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_PASSWORD: str = "admin_password"

    API_V1_STR: str = "/api/v1"
    DATABASE_TYPE: str = "postgres"
    POSTGRES_SERVER: str = "db"
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "app"
    DATABASE_URL: Optional[str] = None
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_URL: Optional[str] = None
    ENVIRONMENT: str = "production"
    IMPORT_UPLOAD_DIR: str = "/app/uploads"

    ICICI_BREEZE_API_KEY: str = ""
    ZERODHA_KITE_API_KEY: str = ""

    # CORS_ORIGINS: str = "http://localhost:3000"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost,http://127.0.0.1:3000,http://10.12.6.254:3000"
    DEBUG: bool = False

    @validator("DATABASE_URL", pre=True, always=True)
    def assemble_db_connection(cls, v, values):
        if values.get("DATABASE_TYPE") == "sqlite":
            return "sqlite:///./arthsaarthi.db"
        if isinstance(v, str):
            return v
        # Default to PostgreSQL if not specified
        return (
            f"postgresql://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}@"
            f"{values.get('POSTGRES_SERVER')}:5432/{values.get('POSTGRES_DB')}"
        )

    @validator("REDIS_URL", pre=True, always=True)
    def assemble_redis_connection(cls, v, values):
        if isinstance(v, str):
            return v
        return f"redis://{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}/0"

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")


settings = Settings(_env_file=None) if os.getenv("TESTING") else Settings()
