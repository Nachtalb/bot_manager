from typing import Any

from pydantic import BaseModel, BaseSettings
import logging


class ApplicationConfig(BaseModel):
    id: str
    module_name: str
    telegram_token: str
    auto_start: bool = False
    arguments: dict[str, Any] = {}


class Config(BaseSettings):
    app_configs: list[ApplicationConfig]

    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    uvicorn_args: dict[str, Any] = {}

    class Config:
        env_file = "config.json"

    @property
    def log_level_int(self):
        return logging._nameToLevel[self.log_level.upper()]


config = Config()  # pyright: ignore[reportGeneralTypeIssues]
