import importlib
from asyncio import gather
from logging import getLogger
from types import ModuleType
from typing import Iterable, Type


from bots.applications._base import Application
from bots.config import config

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

    # =========
    # LIFECYCLE
    # =========

    async def load_app(self, app_id: str) -> Application:
        """Load app into existence

        Imports or reloads (if already imported) the app module and then
        creates and app instance.
        """
        if app_id in self.apps:
            raise ValueError(f"Application already loaded")

        app_config = config.app_config(app_id)
        if not app_config:
            raise IndexError(f"Application with ID {app_id} not found.")

        self.apps[app_config.id] = app = self._get_application_class(app_config.module)(self, app_config)
        return app

    async def load_apps(self, app_ids: Iterable[str] = []) -> list[Application]:
        """Load all or given apps into existence"""
        if not app_ids:
            app_ids = [app.id for app in config.app_configs]
        return await gather(*[self.load_app(app) for app in app_ids or self.apps.keys()])

    async def initialize_app(self, app: Application) -> Application:
        """Initialize an app

        Initialize the app via app.initialize() and add the api router to the server
        """
        await app.initialize()
        return app

    async def initialize_apps(self, apps: Iterable[Application] = []) -> list[Application]:
        """Initialize all or given apps"""
        return await gather(*[self.initialize_app(app) for app in apps or self.apps.values()])

    async def start_app(self, app: Application) -> Application:
        """Start an app"""
        await app.start()
        return app

    async def start_apps(self, apps: Iterable[Application] = []) -> list[Application]:
        """Start all or given apps"""
        return await gather(*[self.start_app(app) for app in apps or self.apps.values()])

    async def pause_app(self, app: Application) -> Application:
        """Pause an app"""
        await app.pause()
        return app

    async def pause_apps(self, apps: Iterable[Application] = []) -> list[Application]:
        """Pause all or given apps"""
        return await gather(*[self.pause_app(app) for app in apps or self.apps.values()])

    async def shutdown_app(self, app: Application) -> Application:
        """Shutdown an app

        Includes filtering the web api requests. It's not possible to remove the
        router due to limitations of FastAPI, but at least we can filter them.
        """
        await app.shutdown()
        return app

    async def shutdown_apps(self, apps: Iterable[Application] = []) -> list[Application]:
        """Shutdown all or given apps"""
        return await gather(*[self.shutdown_app(app) for app in apps or self.apps.values()])

    async def destroy_app(self, app_id: str) -> str:
        """Destroy an app

        Shutdown the app then completely delete it
        """
        app = self.apps[app_id]
        await self.shutdown_app(app)
        del self.apps[app.id]
        return app_id

    async def destroy_apps(self, app_ids: Iterable[str] = []) -> list[Application]:
        """Destroy all or given apps"""
        return await gather(*[self.destroy_app(app) for app in app_ids or self.apps.keys()])

    async def _pure_reload_app(self, app_id: str) -> Application:
        """Destroy and load an app"""
        await self.destroy_app(app_id)
        return await self.load_app(app_id)

    async def reload_app(self, app_id: str, update_config: bool = True) -> Application:
        """Reload and app

        Update app config if needed, then doestroy and reload the app and
        lastely restart the app if it was started beforehand
        """
        if update_config:
            config.reload_app_config(app_id)

        start_again = self.apps[app_id].running
        app = await self._pure_reload_app(app_id)
        await self.initialize_app(app)

        if start_again:
            await self.start_app(app)
        return app

    async def reload_apps(self, app_ids: Iterable[str] = []) -> list[Application]:
        """Reload all or given apps"""
        running = {app_id: self.apps[app_id].running for app_id in app_ids or self.apps.keys()}
        if not app_ids:
            await self.destroy_apps()
            config.reload_config()
            apps = await self.load_apps()
            await self.initialize_apps(apps)
        else:
            apps = await gather(*[self.reload_app(app_id, False) for app_id in app_ids])

        await gather(*[self.start_app(app) for app in apps if running.get(app.id, app.auto_start)])
        return apps


app_manager = AppManager()
