import asyncio
from importlib import reload
import os
import signal

from fastapi import APIRouter

from bots.applications import applications, _base
from bots.applications import reload_app as reload_application
from bots.applications import destroy_all as destroy_all_applications
from bots.applications import load_applications
from bots.applications import start_all as start_all_applications
from bots.applications import stop_all as stop_all_applications
from bots.config import Config, config
from bots.log import log, runtime_logs
from bots.utils import safe_error

router = APIRouter()


sync_lock = asyncio.Lock()


@router.get("/shutdown")
@safe_error
async def shutdown_server():
    await destroy_all_applications()
    os.kill(os.getpid(), signal.SIGINT)


@router.get("/logs")
@safe_error
@log(ignore_incoming=True)
async def list_logs(since: int = 0):
    filtered_logs = runtime_logs
    if since:
        filtered_logs = tuple(entry for entry in runtime_logs if entry["timestamp"] >= since)

    return {"status": "success", "logs": filtered_logs}


@router.get("/reload_config")
@safe_error
@log()
async def reload_config():
    async with sync_lock:
        active = [id for id, app in applications.items() if app.running]
        await destroy_all_applications()
        reload(_base)
        new_config = Config.parse_file("config.json")
        config.app_configs = new_config.app_configs
        await load_applications()
        asyncio.gather(*[app.start_application() for id, app in applications.items() if id in active])
        return {"status": "success"}


@router.get("/start_all")
@safe_error
@log()
async def start_all():
    await start_all_applications()
    return {"status": "success"}


@router.get("/stop_all")
@safe_error
@log()
async def stop_all():
    await stop_all_applications()
    return {"status": "success"}


@router.post("/start_app/{app_id}")
@safe_error
@log(["app_id"])
async def start_app(app_id: str):
    try:
        app = applications[app_id]
        await app.start_application()
        return {"status": "success", "message": f"Started app with ID {app_id}"}
    except IndexError:
        return {"status": "error", "message": f"No app found with ID {app_id}"}


@router.post("/restart_app/{app_id}")
@safe_error
@log(["app_id"])
async def restart_app(app_id: str):
    try:
        app = applications[app_id]
        await app.stop_application()
        await app.start_application()
        return {"status": "success", "message": f"Restarted app with ID {app_id}"}
    except IndexError:
        return {"status": "error", "message": f"No app found with ID {app_id}"}


@router.post("/reload_app/{app_id}")
@safe_error
@log(["app_id"])
async def reload_app(app_id: str):
    if app_id not in applications:
        return {"status": "error", "message": f"No app found with ID {app_id}"}
    async with sync_lock:
        await reload_application(app_id)
    return {"status": "success", "message": f"Reloaded app with ID {app_id}"}


@router.post("/stop_app/{app_id}")
@safe_error
@log(["app_id"])
async def stop_app(app_id: str):
    try:
        app = applications[app_id]
        await app.stop_application()
        return {"status": "success", "message": f"Stopped app with ID {app_id}"}
    except IndexError:
        return {"status": "error", "message": f"No app found with ID {app_id}"}


@router.get("/list")
@safe_error
@log(ignore_incoming=True)
async def list_applications():
    async with sync_lock:
        return {"status": "success", "applications": [await _app_info(app) for app in applications.values()]}


async def _app_info(app: _base.ApplicationWrapper) -> dict[str, Any]:
    bot = await app.get_bot()
    bot_dict = bot.to_dict()
    bot_dict["link"] = bot.link

    return {
        "id": app.id,
        "telegram_token": app.config.telegram_token,
        "running": app.running,
        "bot": bot_dict,
        "config": json.loads(app.arguments.json()),
    }


@router.get("/app/{app_id}")
@safe_error
@log(ignore_incoming=True)
async def get_app(app_id: str):
    app = applications.get(app_id)
    if not app:
        return {"status": "error", "message": f"No app found with ID {app_id}"}

    return {"status": "success", "data": await _app_info(app)}
