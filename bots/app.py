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
from bots.log import LogEntry, runtime_logs
from bots.utils import Namespace

app = FastAPI()
manager: SocketManager = SocketManager(app)

logging.basicConfig(
    level=config.global_log_level_int,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
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

    async def on_connect(self, sid: str, environ: dict) -> None:
        await super().on_connect(sid, environ)
        await self.emit_success("connect", "Connection established")

    async def on_shutdown(self, _: str):
        await app_manager.destroy_all()
        await self.emit_success("shutdown", "Stopped all apps and shutting down now...")
        os.kill(os.getpid(), signal.SIGINT)


app.sio.register_namespace(ServerNamespace())  # pyright: ignore[reportGeneralTypeIssues]
app.sio.register_namespace(ApiNamespace())  # pyright: ignore[reportGeneralTypeIssues]
