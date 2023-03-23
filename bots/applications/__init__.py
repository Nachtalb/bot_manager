import asyncio
import importlib
from logging import getLogger
from types import ModuleType
from typing import Iterable, Type

from bots.applications._base import Application
from bots.config import CONFIG_FILE, Config, config

logger = getLogger("application_manager")
logger.setLevel(config.local_log_level)


class AppManager:
    def __init__(self):
        self._modules: dict[str, ModuleType] = {}
        self.apps: dict[str, Application] = {}

    def _load_module(self, module_path: str) -> tuple[str, ModuleType]:
        module_path = module_path.split(":", 1)[0]

        if "." not in module_path:
            module_path = "bots.applications." + module_path

        if module_path not in self._modules:
            logger.info(f"Loading {module_path}")
            self._modules[module_path] = module = importlib.import_module(module_path)
        else:
            logger.info(f"Reloading {module_path}")
            self._modules[module_path] = module = importlib.reload(self._modules[module_path])

        return module_path, module

    def _get_application_class(self, module_full_path: str) -> Type[Application]:
        name = module_full_path.split(":", 1)[1] if ":" in module_full_path else "Application"
        module_path, module = self._load_module(module_full_path)

        try:
            return getattr(module, name)
        except AttributeError:
            raise ImportError(f"Cannot import name '{name}' from '{module}'", name=module_path, path=module.__file__)

    async def start_all(self):
        await asyncio.gather(*[app.start() for app in self.apps.values()])

    async def stop_all(self):
        await asyncio.gather(*[app.stop() for app in self.apps.values()])

    async def restart_all(self):
        await self.stop_all()
        await self.start_all()

    async def destroy(self, app_id: str):
        app = self.apps[app_id]
        await app.stop()
        await app.teardown()
        del self.apps[app.id]

    async def load(self, app_id: str, run_setup: bool = True) -> Application:
        if app_id in self.apps:
            raise ValueError(f"Application already loaded")

        app_config = config.app_config(app_id)
        if not app_config:
            raise IndexError(f"Application with ID {app_id} not found.")

        self.apps[app_config.id] = app = self._get_application_class(app_config.module)(self, app_config)
        if run_setup:
            await app.setup()
        return app

    async def load_all(self) -> Iterable[Application]:
        for app_config in config.app_configs:
            await self.load(app_config.id, False)
        await asyncio.gather(*[app.setup() for app in self.apps.values()])
        return self.apps.values()

    async def destroy_all(self):
        await asyncio.gather(*[self.destroy(app_id) for app_id in self.apps])

    async def reload(self, app_id: str):
        was_on = self.apps[app_id].running
        await self.destroy(app_id)

        new_app_config = Config.parse_file(CONFIG_FILE).app_config(app_id)
        if not new_app_config:
            raise ValueError(f"No config found for app with ID {app_id}")

        config.set_app_config(new_app_config)

        app = await self.load(app_id)

        if was_on:
            await app.start()
        return app

    async def reload_all(self):
        new_config = Config.parse_file(CONFIG_FILE)
        for field, value in new_config:
            setattr(config, field, value)

        were_on = [app.id for app in self.apps.values() if app.running]
        await self.destroy_all()
        await self.load_all()

        await asyncio.gather(*[self.apps[app_id].start() for app_id in were_on])


app_manager = AppManager()
