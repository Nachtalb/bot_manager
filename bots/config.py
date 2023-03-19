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
    global_log_level: str = "WARNING"
    local_log_level: str = "INFO"
    web_log_level: str = "INFO"

    uvicorn_args: dict[str, Any] = {}

    def _log_level_int(self, level: str) -> int:
        return logging._nameToLevel[level.upper()]

    @property
    def global_log_level_int(self):
        return self._log_level_int(self.global_log_level)

    @property
    def local_log_level_int(self):
        return self._log_level_int(self.local_log_level)

    @property
    def web_log_level_int(self):
        return self._log_level_int(self.web_log_level)


config = Config.parse_file("config.json")
