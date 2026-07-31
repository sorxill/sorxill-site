"""Единственная точка чтения окружения. Падает на старте, а не в рантайме."""

import json
from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["local", "ci", "production"] = "local"
    database_url: str = "postgresql+asyncpg://sorxill:local@localhost:5432/sorxill"
    app_version: str = "dev"
    log_level: str = "INFO"
    # NoDecode обязателен: без него pydantic-settings пытается разобрать
    # значение как JSON ДО валидатора и падает на обычной строке
    # "https://a.ru,https://b.ru".
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)
    contact_persist: bool = False

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split(cls, v: object) -> object:
        """Принимает и "a,b", и '["a","b"]' — compose даёт первое, а
        привычка писать JSON в ENV встречается достаточно часто."""
        if isinstance(v, str):
            raw = v.strip()
            if raw.startswith("["):
                parsed = json.loads(raw)
                return [str(o).strip() for o in parsed]
            return [o.strip() for o in raw.split(",") if o.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
