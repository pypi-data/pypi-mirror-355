
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


# See: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
class Settings(BaseSettings):
    DATABASE_DATA_PATH: str = ".dev/track_data"
    DATABASE_PATH: str = ".dev/track_data/sigmavest-invest.duckdb"
    DEPENDENCY_AUTO_REGISTER: list = ["sigmavest.invest.dependency"]

    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    MAGIC_FORMULA_USERNAME: str = ""
    MAGIC_FORMULA_PASSWORD: str = ""
    MAGIC_FORMULA_MIN_MARKET_CAP: int = 50

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Cache settings for better performance"""
    return Settings()
