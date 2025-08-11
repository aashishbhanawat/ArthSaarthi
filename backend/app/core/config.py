from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SECRET_KEY: str = "a_super_secret_key_that_should_be_changed"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./pms_local.db"
    REDIS_URL: str = "redis://redis:6379/0"
    ENVIRONMENT: str = "production"
    SERVE_STATIC_FRONTEND: bool = False
    IMPORT_UPLOAD_DIR: str = "/app/uploads"

    ICICI_BREEZE_API_KEY: str = ""
    ZERODHA_KITE_API_KEY: str = ""

    # CORS_ORIGINS: str = "http://localhost:3000"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost,http://127.0.0.1:3000,http://10.12.6.254:3000"
    DEBUG: bool = False

    model_config = SettingsConfigDict(case_sensitive=True)


settings = Settings()
