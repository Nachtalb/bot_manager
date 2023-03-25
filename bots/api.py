import asyncio
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from bots.applications import _base, app_manager
from bots.config import ApplicationConfig, config
from bots.utils import Namespace, serialised_dict

sync_lock = asyncio.Lock()


class ApiNamespace(Namespace):
    namespace = "/api"

    async def app_info(self, app: _base.Application) -> dict[str, Any]:
        bot = await app.get_me()
        bot_dict = bot.to_dict()
        bot_dict["link"] = bot.link

        return {
            "id": app.id,
            "telegram_token": app.config.telegram_token,
            "running": app.running,
            "bot": bot_dict,
            "config": json.loads(app.arguments.json(exclude_defaults=True)),
            "fields": {
                name: {
                    "type": field.type_.__name__,
                    "default": field.get_default(),
                    "required": field.required,
                }
                for name, field in app.Arguments.__fields__.items()
            },
        }

    async def apps_info(self) -> list[dict[str, Any]]:
        return [await self.app_info(app) for app in app_manager.apps.values()]

    async def on_connect(self, sid: str, environ: dict) -> None:
        await super().on_connect(sid, environ)
        await self.emit_success("connect", "Connection established", {"apps_update": await self.apps_info()})

    # ================
    # ACTIONS ALL APPS
    # ================

    async def on_apps_reload(self, _: str):
        async with sync_lock:
            await app_manager.reload_all()

        await self.emit_success("apps_reload", "Apps reloaded", {"apps_update": await self.apps_info()})

    async def on_apps_restart(self, _: str):
        async with sync_lock:
            await app_manager.restart_all()
        await self.emit_success("apps_restart", "Apps restarted", {"apps_update": await self.apps_info()})

    async def on_apps_start(self, _: str):
        async with sync_lock:
            await app_manager.start_all()
        await self.emit_success("apps_start", "Apps started", {"apps_update": await self.apps_info()})

    async def on_apps_stop(self, _: str):
        async with sync_lock:
            await app_manager.stop_all()
        await self.emit_success("apps_stop", "Apps stopped", {"apps_update": await self.apps_info()})

    # ==================
    # ACTIONS SINGLE APP
    # ==================

    async def get_app_or_send_error(self, event: str, sid: str, app_id: str | None) -> _base.Application | None:
        if app_id and (app := app_manager.apps.get(app_id)):
            return app
        await self.emit_error(event, message=f"App with ID {app_id} not found!", sid=sid)

    async def on_app_reload(self, sid: str, data: dict):
        app = await self.get_app_or_send_error("app_reload", sid, data.get("appId"))
        if not app:
            return

        async with sync_lock:
            app = await app.reload()

        await self.emit_success("app_reload", f"App {app.id} reloaded", {"app_update": await self.app_info(app)})

    async def on_app_restart(self, sid: str, data: dict):
        app = await self.get_app_or_send_error("app_restart", sid, data.get("appId"))
        if not app:
            return

        async with sync_lock:
            await app.restart()

        await self.emit_success("app_restart", f"App {app.id} restarted", {"app_update": await self.app_info(app)})

    async def on_app_start(self, sid: str, data: dict):
        app = await self.get_app_or_send_error("app_start", sid, data.get("appId"))
        if not app:
            return

        async with sync_lock:
            await app.start()

        await self.emit_success("app_start", f"App {app.id} started", {"app_update": await self.app_info(app)})

    async def on_app_stop(self, sid: str, data: dict):
        app = await self.get_app_or_send_error("app_stop", sid, data.get("appId"))
        if not app:
            return

        async with sync_lock:
            await app.stop()

        await self.emit_success("app_stop", f"App {app.id} stopped", {"app_update": await self.app_info(app)})

    async def on_app_edit(self, sid: str, data: dict):
        app_id = data.get("appId")
        app = await self.get_app_or_send_error("app_edit", sid, app_id)
        if not app:
            return

        new_config = data.get("config")
        if new_config is None:
            return await self.emit_error("app_edit", message='"config" not set!')
        old_config = serialised_dict(app.arguments, exclude_defaults=True)

        try:
            parsed_config = app.Arguments.parse_obj(new_config)
        except ValidationError as error:
            return await self.emit_error("app_edit", message=f"Config validation error: {error}")

        if app.arguments == parsed_config:
            return await self.emit_warning("app_edit", "Nothing has changed")

        async with sync_lock:
            app_config: ApplicationConfig = config.app_config(app_id)  # pyright: ignore[reportGeneralTypeIssues]
            app_config.arguments = serialised_dict(parsed_config, exclude_defaults=True)

            config.set_app_config(app_config)

            Path("config.json").write_text(config.json(ensure_ascii=False, sort_keys=True, indent=2))

            app = await app.reload()

        await self.emit_success(
            "app_edit",
            f"App {app.id} edited and reloaded",
            {
                "app_update": await self.app_info(app),
                "new_config": serialised_dict(app.arguments, exclude_defaults=True),
                "old_config": old_config,
            },
        )

    # ====
    # READ
    # ====

    async def on_apps_config(self, _: str):
        async with sync_lock:
            await self.emit_success(
                "all_app_configs",
                "All app info retrieved",
                {"apps_update": [await self.app_info(app) for app in app_manager.apps.values()]},
            )

    async def on_app_config(self, sid: str, data: dict):
        app = await self.get_app_or_send_error("app_config", sid, data.get("appId"))
        if not app:
            return

        await self.emit_success("single_app_config", "App info retrieved", {"app_update": await self.app_info(app)})
