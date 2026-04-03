import secrets
from typing import Literal, Optional

from pydantic import Field, validator

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    # Fallback for pydantic v1 (used on Android)
    from pydantic import BaseSettings
    SettingsConfigDict = None


def _is_local_mode(values: dict) -> bool:
    """Check if running in a local/embedded mode (desktop or android)."""
    return values.get("DEPLOYMENT_MODE") in ("desktop", "android") or \
           values.get("DATABASE_TYPE") == "sqlite"


class Settings(BaseSettings):
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Default admin user
    ADMIN_USERNAME: str = "admin"
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_PASSWORD: str = "admin_password"
    FIRST_SUPERUSER: str = "admin@example.com"
    FIRST_SUPERUSER_PASSWORD: str = "a-secure-password!123"

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
    CACHE_TYPE: Literal["redis", "disk"] = "redis"
    DEPLOYMENT_MODE: Literal["server", "desktop", "android"] = "server"
    ENVIRONMENT: str = "production"
    IMPORT_UPLOAD_DIR: str = "uploads"
    DISK_CACHE_DIR: Optional[str] = None
    LOG_DIR: Optional[str] = None
    LOG_FILE: Optional[str] = None

    ICICI_BREEZE_API_KEY: str = ""
    ZERODHA_KITE_API_KEY: str = ""

    # CORS_ORIGINS: str = "http://localhost:3000"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost,http://127.0.0.1:3000"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # For desktop encryption
    ENCRYPTION_KEY_PATH: str = "master.key"
    WRAPPED_KEY_PATH: str = "master.key.wrapped"

    @validator("DATABASE_URL", pre=True, always=True)
    def assemble_db_connection(cls, v, values):
        if _is_local_mode(values):
            # If a DATABASE_URL is already provided (e.g., by Android launcher),
            # use it as-is
            if isinstance(v, str) and v.startswith("sqlite"):
                return v
            from platformdirs import user_data_dir
            from pathlib import Path
            # Use a stable, platform-appropriate directory for the database
            app_dir = Path(user_data_dir("arthsaarthi", "arthsaarthi-app"))
            app_dir.mkdir(parents=True, exist_ok=True)
            db_path = app_dir / "arthsaarthi.db"
            return f"sqlite:///{db_path.resolve()}"

        if isinstance(v, str):
            return v
        # Default to PostgreSQL if not specified
        return (
            f"postgresql://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}@"
            f"{values.get('POSTGRES_SERVER')}:5432/{values.get('POSTGRES_DB')}"
        )

    @validator("CACHE_TYPE", pre=True, always=True)
    def set_cache_type_for_desktop(cls, v, values):
        if _is_local_mode(values):
            return "disk"
        return v

    @validator("IMPORT_UPLOAD_DIR", pre=True, always=True)
    def set_upload_dir_for_desktop(cls, v, values):
        if values.get("DEPLOYMENT_MODE") in ("desktop", "android"):
            from platformdirs import user_data_dir
            from pathlib import Path
            # Use a stable directory for uploads
            upload_dir = Path(user_data_dir("arthsaarthi", "arthsaarthi-app")) / "uploads"
            upload_dir.mkdir(parents=True, exist_ok=True)
            return str(upload_dir)
        return v

    @validator("DISK_CACHE_DIR", pre=True, always=True)
    def set_disk_cache_dir_for_desktop(cls, v, values):
        if _is_local_mode(values):
            if isinstance(v, str):
                return v
            from platformdirs import user_cache_dir
            from pathlib import Path
            # Use a stable directory for cache
            cache_dir = Path(user_cache_dir("arthsaarthi", "arthsaarthi-app"))
            cache_dir.mkdir(parents=True, exist_ok=True)
            return str(cache_dir)
        return v

    @validator("LOG_DIR", pre=True, always=True)
    def set_log_dir_for_desktop(cls, v, values):
        if _is_local_mode(values):
            if isinstance(v, str):
                return v
            from platformdirs import user_log_dir
            from pathlib import Path
            # Use a stable directory for logs
            log_dir = Path(user_log_dir("arthsaarthi", "arthsaarthi-app"))
            log_dir.mkdir(parents=True, exist_ok=True)
            return str(log_dir)
        return v

    @validator("LOG_FILE", pre=True, always=True)
    def set_log_file_for_desktop(cls, v, values):
        if _is_local_mode(values):
            if isinstance(v, str):
                return v
            from pathlib import Path
            log_dir = Path(values.get("LOG_DIR"))
            return str(log_dir / "arthsaarthi.log")
        return v

    @validator("REDIS_URL", pre=True, always=True)
    def assemble_redis_connection(cls, v, values):
        if isinstance(v, str):
            return v
        return f"redis://{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}/0"

    if SettingsConfigDict:
        model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")
    else:
        class Config:
            case_sensitive = True
            env_file = ".env"


settings = Settings()
