import asyncio
import logging
import os
import signal
import time

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi_socketio import SocketManager

from bots.api import ApiNamespace
from bots.applications import app_manager
from bots.config import config
from bots.log import LogEntry, SocketLogHandler, runtime_logs
from bots.utils import Namespace

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


# Add these lines to serve the 'index.html' file from the 'static' folder
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def get_index():
    with open("public/index.html", "r") as f:
        content = f.read()
    return content


@app.on_event("shutdown")
async def on_shutdown():
    await app_manager.destroy_all()


@app.on_event("startup")
async def on_startup():
    apps = await app_manager.load_all()
    for task in asyncio.as_completed([app.start() for app in apps if app.auto_start]):
        app = await task
        entry = LogEntry(text=f"{app.name} auto started", status="success", timestamp=int(time.time()))
        logger.info(entry["text"])
        runtime_logs.append(entry)


class ServerNamespace(Namespace):
    namespace = "/server"

    def __init__(self, log_queue: asyncio.Queue, namespace=None):
        super().__init__(namespace)

        self.log_queue = log_queue
        self.log_emitter = asyncio.create_task(self.log_emitter_loop())

    async def log_emitter_loop(self):
        try:
            while True:
                item: dict = await self.log_queue.get()
                await self.emit_default("log", **item)
                self.log_queue.task_done()
        except asyncio.CancelledError:
            pass

    async def on_connect(self, sid: str, environ: dict) -> None:
        await super().on_connect(sid, environ)
        await self.emit_success("connect", "Connection established")

    async def on_shutdown(self, _: str):
        await app_manager.destroy_all()
        await self.emit_success("shutdown", "Stopped all apps and shutting down now...")
        os.kill(os.getpid(), signal.SIGINT)


app.sio.register_namespace(ServerNamespace(socket_log_handler.queue))  # pyright: ignore[reportGeneralTypeIssues]
app.sio.register_namespace(ApiNamespace())  # pyright: ignore[reportGeneralTypeIssues]
