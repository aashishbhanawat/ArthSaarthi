from pydantic import PostgresDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = "a_very_secret_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE_URL: PostgresDsn
    CORS_ORIGINS: str = "http://localhost:3000"

    class Config:
        # pydantic-settings will automatically read from environment variables
        # The .env file is loaded by docker-compose
        pass

settings = Settings()