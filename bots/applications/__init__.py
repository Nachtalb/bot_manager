import asyncio
import importlib
import json
from types import ModuleType
from typing import Type

from bots.applications._base import ApplicationWrapper

applications: dict[str, ApplicationWrapper] = {}
_modules: dict[str, ModuleType] = {}


async def load_applications():
    with open("config.json", "r") as f:
        configs = json.load(f)

    for config in configs:
        module_name = config["module_name"]
        telegram_token = config["telegram_token"]
        _id = config["id"]
        auto_start = config.get("auto_start", False)
        kwargs = config.get("arguments", {})

        if _id in applications:
            raise ValueError("Duplicate bot ID")

        module_path = f"bots.applications.{module_name}"
        if module_path not in _modules:
            _modules[module_path] = importlib.import_module(module_path)
        else:
            _modules[module_path] = importlib.reload(_modules[module_path])

        app_class: Type[ApplicationWrapper] = getattr(_modules[module_path], "Application")
        app_instance = app_class(telegram_token, _id, auto_start, kwargs)
        applications[app_instance.id] = app_instance
    asyncio.gather(*[app.setup(**app.setup_args) for app in applications.values()])


async def start_all():
    asyncio.gather(*[app.start_application() for app in applications.values()])


async def stop_all():
    asyncio.gather(*[app.stop_application() for app in applications.values()])


async def destroy_all():
    await stop_all()
    asyncio.gather(*[app.teardown() for app in applications.values()])
    applications.clear()
