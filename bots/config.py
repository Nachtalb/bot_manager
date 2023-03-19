from typing import Any

from pydantic import BaseModel, BaseSettings


class ApplicationConfig(BaseModel):
    id: str
    module_name: str
    telegram_token: str
    auto_start: bool = False
    arguments: dict[str, Any] = {}


class Config(BaseSettings):
    app_configs: list[ApplicationConfig]

    class Config:
        env_file = "config.json"


config = Config()  # pyright: ignore[reportGeneralTypeIssues]
