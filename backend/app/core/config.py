import secrets
from pathlib import Path
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


def _get_app_dir() -> Path:
    from platformdirs import user_data_dir

    new_dir = Path(user_data_dir("arthsaarthi", "arthsaarthi-app"))
    new_dir.mkdir(parents=True, exist_ok=True)

    # Legacy migration check: v1.2.0 stored database in ~/.arthsaarthi/arthsaarthi.db
    legacy_dir = Path.home() / ".arthsaarthi"
    legacy_db = legacy_dir / "arthsaarthi.db"
    new_db = new_dir / "arthsaarthi.db"

    if legacy_db.exists() and not new_db.exists():
        import logging
        import shutil

        logger = logging.getLogger(__name__)
        logger.info(
            f"Migrating legacy v1.2.0 database from {legacy_db} to {new_dir}..."
        )
        try:
            shutil.copy2(legacy_db, new_db)
            legacy_uploads = legacy_dir / "uploads"
            new_uploads = new_dir / "uploads"
            if legacy_uploads.exists() and not new_uploads.exists():
                shutil.copytree(legacy_uploads, new_uploads)

            for key_file in ("master.key", "master.key.wrapped", "secret.key"):
                legacy_key = legacy_dir / key_file
                new_key = new_dir / key_file
                if legacy_key.exists() and not new_key.exists():
                    shutil.copy2(legacy_key, new_key)

            logger.info("Legacy v1.2.0 data migration completed successfully.")
        except Exception as e:
            logger.error(f"Failed to migrate legacy data from {legacy_dir}: {e}")

    return new_dir


def _get_or_create_secret_key() -> str:
    """
    Returns a persistent secret key for local/desktop/android deployments.
    Prevents JWT token signature verification failures across application restarts.
    """
    try:
        app_dir = _get_app_dir()
        key_file = app_dir / "secret.key"
        if key_file.exists():
            stored_key = key_file.read_text().strip()
            if stored_key:
                return stored_key

        new_key = secrets.token_urlsafe(32)
        key_file.write_text(new_key)
        return new_key
    except Exception:
        return secrets.token_urlsafe(32)


class Settings(BaseSettings):
    SECRET_KEY: str = Field(default_factory=_get_or_create_secret_key)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

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

            # Use a stable, platform-appropriate directory for the database
            app_dir = _get_app_dir()
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
            # Use a stable directory for uploads
            upload_dir = _get_app_dir() / "uploads"
            upload_dir.mkdir(parents=True, exist_ok=True)
            return str(upload_dir)
        return v

    @validator("DISK_CACHE_DIR", pre=True, always=True)
    def set_disk_cache_dir(cls, v, values):
        if isinstance(v, str):
            return v
        from pathlib import Path
        if _is_local_mode(values):
            from platformdirs import user_cache_dir
            # Use a stable directory for cache
            cache_dir = Path(user_cache_dir("arthsaarthi", "arthsaarthi-app"))
        else:
            # Server/Docker mode: use /tmp or a dedicated volume path
            cache_dir = Path("/tmp/arthsaarthi/cache")
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            # Fallback for restricted environments
            return "/tmp"
        return str(cache_dir)

    @validator("LOG_DIR", pre=True, always=True)
    def set_log_dir_for_desktop(cls, v, values):
        if _is_local_mode(values):
            if isinstance(v, str):
                return v
            from pathlib import Path

            from platformdirs import user_log_dir
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
