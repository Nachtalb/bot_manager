from typing import Any

from pydantic import BaseModel
import logging


class ApplicationConfig(BaseModel):
    id: str
    module: str
    telegram_token: str
    auto_start: bool = False
    arguments: dict[str, Any] = {}


class Config(BaseModel):
    app_configs: list[ApplicationConfig]

    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    uvicorn_args: dict[str, Any] = {}

    @property
    def log_level_int(self):
        return logging._nameToLevel[self.log_level.upper()]


config = Config.parse_file("config.json")
