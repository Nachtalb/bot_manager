import asyncio
import importlib
from types import ModuleType
from typing import Type

from bots.config import config

from bots.applications._base import ApplicationWrapper

applications: dict[str, ApplicationWrapper] = {}
_modules: dict[str, ModuleType] = {}


async def load_applications(app_id: str | None = None):
    for app_config in config.app_configs:
        if app_id and app_config.id != app_id:
            continue

        if app_config.id in applications:
            raise ValueError("Duplicate bot ID")

        name: str = "Application"
        module_path = app_config.module
        if ":" in app_config.module:
            module_path, name = app_config.module.split(":", 1)

        if "." not in module_path:
            module_path = "bots.applications." + module_path

        try:
            if module_path not in _modules:
                _modules[module_path] = importlib.import_module(module_path)
            else:
                _modules[module_path] = importlib.reload(_modules[module_path])
        except ImportError:
            raise ModuleNotFoundError(
                f"No module named {module_path} for application {app_config.id}", name=module_path
            )

        try:
            app_class: Type[ApplicationWrapper] = getattr(_modules[module_path], name)
        except AttributeError:
            raise ImportError(
                f"Cannot import name '{name}' from '{module_path}' for application {app_config.id}",
                name=module_path,
                path=_modules[module_path].__file__,
            )

        app_instance = app_class(app_config)
        applications[app_instance.id] = app_instance
    asyncio.gather(*[app.setup() for app in applications.values()])


async def start_all():
    asyncio.gather(*[app.start_application() for app in applications.values()])


async def stop_all():
    asyncio.gather(*[app.stop_application() for app in applications.values()])


async def destroy(app_id: str):
    app = applications[app_id]
    await app.stop_application()
    await app.teardown()
    del applications[app_id]


async def destroy_all():
    await stop_all()
    asyncio.gather(*[app.teardown() for app in applications.values()])
    applications.clear()
