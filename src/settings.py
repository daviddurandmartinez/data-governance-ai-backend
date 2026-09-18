import os
from pathlib import Path

from dotenv import dotenv_values
from pydantic_settings import BaseSettings, SettingsConfigDict

SRC_DIR = Path(__file__).resolve().parent.parent
_env_vars = dotenv_values(SRC_DIR / ".env")
os.environ.update({k: v for k, v in _env_vars.items() if v is not None})


class Settings(BaseSettings):
    SQL_SERVER_HOST: str = ""
    SQL_SERVER_PORT: int = 1433
    SQL_SERVER_USER: str = ""
    SQL_SERVER_PASSWORD: str = ""

    GROQ_API_KEY: str = ""

    CATALOG_DB_HOST: str = "localhost"
    CATALOG_DB_PORT: int = 1433
    CATALOG_DB_NAME: str = "data_governance_catalog"
    CATALOG_DB_USER: str = ""
    CATALOG_DB_PASSWORD: str = ""

    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def is_db_discovery_enabled(self) -> bool:
        return bool(self.SQL_SERVER_HOST and self.SQL_SERVER_USER and self.SQL_SERVER_PASSWORD)

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    model_config = SettingsConfigDict(
        extra="allow",
    )


settings = Settings()
