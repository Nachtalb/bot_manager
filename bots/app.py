import asyncio
import logging
import time

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from bots.applications import applications
from bots.applications import destroy_all as destroy_all_applications
from bots.applications import load_applications
from bots.api import router
from bots.log import runtime_logs, LogEntry

app = FastAPI()

app.include_router(router)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("bot_manager")


# Add these lines to serve the 'index.html' file from the 'static' folder
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def get_index():
    with open("public/index.html", "r") as f:
        content = f.read()
    return content


@app.on_event("shutdown")
async def on_shutdown():
    await destroy_all_applications()


@app.on_event("startup")
async def on_startup():
    await load_applications()
    for task in asyncio.as_completed([app.start_application() for app in applications.values() if app.auto_start]):
        app = await task
        entry = LogEntry(text=f"{app.name} auto started", status="success", timestamp=int(time.time()))
        logger.info(entry["text"])
        runtime_logs.append(entry)
