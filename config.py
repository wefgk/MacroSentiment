from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List,Any
from pydantic import field_validator

class Settings(BaseSettings):
    AI_URL:str
    API_KEY:str
    BATCH_SIZE:int
    URLS: List[str] | Any
    DB_PATH:str
    ENABLE_SCHEDULER: bool
    INTERVAL_MINUTES: int

    @field_validator("URLS", mode="before")
    @classmethod
    def parsing_by_comma(cls, value: str | list) -> list[str]:
        if isinstance(value, str):
            return [url.strip() for url in value.split(",") if url.strip()]
        return value

    model_config=SettingsConfigDict(env_file=".env",env_file_encoding="utf-8")

settings=Settings()
