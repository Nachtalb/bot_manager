import asyncio
import importlib.resources
import logging
import os
import signal
import time
from typing import Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi_socketio import SocketManager

from bots.api import ApiNamespace
from bots.applications import app_manager
from bots.config import config
from bots.log import LogEntry, SocketLogHandler, runtime_logs
from bots.utils import Namespace

HERE = importlib.resources.files("bots")

app = FastAPI()
manager: SocketManager = SocketManager(app)

socket_log_handler = SocketLogHandler()
socket_log_handler.setFormatter(logging.Formatter("%(name)s: %(message)s"))

logging.basicConfig(
    level=config.global_log_level_int,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(), socket_log_handler],
)

logger = logging.getLogger("bot_manager")
logger.setLevel(config.local_log_level_int)


app_manager.set_server(app)

# Add these lines to serve the 'index.html' file from the 'static' folder
app.mount("/static", StaticFiles(directory=str(HERE / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
async def get_index() -> str:
    return (HERE / "public/index.html").read_text()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await app_manager.destroy_apps()


@app.on_event("startup")
async def on_startup() -> None:
    apps = await app_manager.initialize_apps(await app_manager.load_apps())
    for task in asyncio.as_completed([app_manager.start_app(app) for app in apps if app.auto_start]):
        app = await task
        entry = LogEntry(text=f"{app.name} auto started", status="success", timestamp=int(time.time()))
        logger.info(entry["text"])
        runtime_logs.append(entry)


class ServerNamespace(Namespace):
    namespace = "/server"

    def __init__(self, log_queue: asyncio.Queue[dict[str, Any]], namespace: str | None = None) -> None:
        super().__init__(namespace)

        self.log_queue = log_queue
        self.log_emitter = asyncio.create_task(self.log_emitter_loop())

    async def log_emitter_loop(self) -> None:
        try:
            while True:
                item: dict[str, Any] = await self.log_queue.get()
                await self.emit_default("log", **item)
                self.log_queue.task_done()
        except asyncio.CancelledError:
            pass

    async def on_connect(self, sid: str, environ: dict[str, str]) -> None:
        await super().on_connect(sid, environ)
        await self.emit_success("connect", "Connection established")

    async def on_shutdown(self, _: str) -> None:
        await app_manager.destroy_apps()
        await self.emit_success("shutdown", "Stopped all apps and shutting down now...")
        os.kill(os.getpid(), signal.SIGINT)


app.sio.register_namespace(ServerNamespace(socket_log_handler.queue))  # type: ignore[attr-defined]
app.sio.register_namespace(ApiNamespace())  # type: ignore[attr-defined]
