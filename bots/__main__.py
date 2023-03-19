import uvicorn

from bots.config import config


def main():
    uvicorn.run(
        "bots.app:app",
        host=config.host,
        port=config.port,
        log_level=config.web_log_level_int,
        **config.uvicorn_args,
    )
