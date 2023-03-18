import asyncio
import functools
import logging
import time
from typing import TypedDict

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from bots.applications import applications
from bots.applications import destroy_all as destroy_all_applications
from bots.applications import load_applications
from bots.applications import start_all as start_all_applications
from bots.applications import stop_all as stop_all_applications
from bots.utils import get_arg_value

app = FastAPI()
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("bot_manager")


class LogEntry(TypedDict):
    text: str
    status: str
    timestamp: int


logs: list[LogEntry] = []


def log(arg_names: list[str] = []):
    def decorator_log(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get the function name
            func_name = func.__name__

            # Collect the specified argument names and their values
            arg_values = [f"{name}: {get_arg_value(name, func, args, kwargs)}" for name in arg_names]

            log_text = func_name + (f" - {', '.join(arg_values)}" if arg_names else "")
            log_time = int(time.time())

            # Log the function name and argument names and values in one entry
            try:
                response = await func(*args, **kwargs)
                status = response.get("status", "info") if isinstance(response, dict) else "info"
                entry = LogEntry(text=log_text, status=status, timestamp=log_time)
            except (Exception, BaseException) as error:
                entry = LogEntry(text=log_text + f" - {error}", status="error", timestamp=log_time)
                raise
            except:
                entry = LogEntry(text=log_text, status="error", timestamp=log_time)
                raise
            finally:
                if entry["status"] == "error":
                    logger.warning(entry["text"])
                else:
                    logger.info(entry["text"])
                logs.append(entry)

            return response

        return wrapper

    return decorator_log


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
        logs.append(entry)


@app.get("/logs")
async def list_logs(since: int = 0):
    filtered_logs = logs
    if since:
        filtered_logs = tuple(entry for entry in logs if entry["timestamp"] >= since)

    return {"status": "success", "logs": filtered_logs}


@app.get("/reload_config")
@log()
async def reload_config():
    active = [id for id, app in applications.items() if app.running]
    await destroy_all_applications()
    await load_applications()
    asyncio.gather(*[app.start_application() for id, app in applications.items() if id in active])
    return {"status": "success"}


@app.get("/start_all")
@log()
async def start_all():
    await start_all_applications()
    return {"status": "success"}


@app.get("/stop_all")
@log()
async def stop_all():
    await stop_all_applications()
    return {"status": "success"}


@app.post("/start_app/{app_id}")
@log(["app_id"])
async def start_app(app_id: str):
    try:
        app = applications[app_id]
        await app.start_application()
        return {"status": "success", "message": f"Started app with ID {app_id}"}
    except IndexError:
        return {"status": "error", "message": f"No app found with ID {app_id}"}


@app.post("/stop_app/{app_id}")
@log(["app_id"])
async def stop_app(app_id: str):
    try:
        app = applications[app_id]
        await app.stop_application()
        return {"status": "success", "message": f"Stopped app with ID {app_id}"}
    except IndexError:
        return {"status": "error", "message": f"No app found with ID {app_id}"}


@app.get("/list")
async def list_applications():
    app_list = []
    for id, app in applications.items():
        app_info = {"id": id, "telegram_token": app.telegram_token, "running": app.running}
        app_list.append(app_info)
    return {"status": "success", "applications": app_list}
