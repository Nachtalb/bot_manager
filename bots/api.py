import asyncio
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from bots.applications import _base, app_manager
from bots.config import ApplicationConfig, config
from bots.utils import JsonSerialisableData, Namespace, serialise, serialise_model

sync_lock = asyncio.Lock()


class ApiNamespace(Namespace):
    namespace = "/api"

    async def app_info(self, app: _base.Application) -> JsonSerialisableData:
        bot = await app.get_bot()
        bot_dict = bot.to_dict()
        bot_dict["link"] = bot.link

        type = app.__class__.__name__
        bases = ", ".join([base.__name__ for base in app.__class__.__bases__ if base != _base.Application])
        if bases:
            type += f"[{bases}]"

        config = app.arguments.model_dump(exclude_defaults=True)

        return serialise(
            {
                "id": app.id,
                "telegram_token": app.config.telegram_token,
                "initialized": app.initialized,
                "running": app.running,
                "bot": bot_dict,
                "type": type,
                "config": config,
                "fields": {
                    name: {
                        "type": getattr(field.annotation, "__name__", repr(field.annotation).replace("|", "or")),
                        "help": field.description,
                        "default": field.get_default(),
                        "current": config.get(name, field.get_default()),
                        "required": field.is_required(),
                    }
                    for name, field in app.Arguments.model_fields.items()
                },
            }
        )

    async def apps_info(self) -> list[JsonSerialisableData]:
        return [await self.app_info(app) for app in app_manager.apps.values()]

    async def on_connect(self, sid: str, environ: dict[str, str]) -> None:
        await super().on_connect(sid, environ)
        await self.emit_success("connect", "Connection established", {"apps_update": await self.apps_info()})

    # ================
    # ACTIONS ALL APPS
    # ================

    async def on_apps_reload(self, _: str) -> None:
        async with sync_lock:
            await app_manager.reload_apps()

        await self.emit_success("apps_reload", "Apps reloaded", {"apps_update": await self.apps_info()})

    async def on_apps_start(self, _: str) -> None:
        async with sync_lock:
            await app_manager.start_apps()
        await self.emit_success("apps_start", "Apps started", {"apps_update": await self.apps_info()})

    async def on_apps_pause(self, _: str) -> None:
        async with sync_lock:
            await app_manager.pause_apps()
        await self.emit_success("apps_pause", "Apps paused", {"apps_update": await self.apps_info()})

    # ==================
    # ACTIONS SINGLE APP
    # ==================

    async def get_app_or_send_error(self, event: str, sid: str, app_id: str | None) -> _base.Application | None:
        if app_id and (app := app_manager.apps.get(app_id)):
            return app
        await self.emit_error(event, message=f"App with ID {app_id} not found!", sid=sid)
        return None

    async def on_app_reload(self, sid: str, data: dict[str, Any]) -> None:
        app = await self.get_app_or_send_error("app_reload", sid, data.get("appId"))
        if not app:
            return

        async with sync_lock:
            app = await app_manager.reload_app(app.id)

        await self.emit_success("app_reload", f"App {app.id} reloaded", {"app_update": await self.app_info(app)})

    async def on_app_start(self, sid: str, data: dict[str, Any]) -> None:
        app = await self.get_app_or_send_error("app_start", sid, data.get("appId"))
        if not app:
            return

        async with sync_lock:
            await app_manager.start_app(app)

        await self.emit_success("app_start", f"App {app.id} started", {"app_update": await self.app_info(app)})

    async def on_app_pause(self, sid: str, data: dict[str, Any]) -> None:
        app = await self.get_app_or_send_error("app_pause", sid, data.get("appId"))
        if not app:
            return

        async with sync_lock:
            await app_manager.pause_app(app)

        await self.emit_success("app_pause", f"App {app.id} paused", {"app_update": await self.app_info(app)})

    async def on_app_edit(self, sid: str, data: dict[str, Any]) -> None:
        app_id: str = data.get("appId")  # type: ignore[assignment]
        app = await self.get_app_or_send_error("app_edit", sid, app_id)
        if not app:
            return

        new_config = data.get("config")
        if new_config is None:
            return await self.emit_error("app_edit", message='"config" not set!')
        old_config = serialise_model(app.arguments, exclude_defaults=True)

        try:
            parsed_config = app.Arguments.model_validate(new_config)
        except ValidationError as error:
            return await self.emit_error("app_edit", message=f"Config validation error: {error}")

        if app.arguments == parsed_config:
            return await self.emit_warning("app_edit", "Nothing has changed")

        async with sync_lock:
            app_config: ApplicationConfig = config.app_config(app_id)  # type: ignore[assignment]
            app_config.arguments = serialise_model(parsed_config, exclude_defaults=True)  # type: ignore[assignment]
            config.set_app_config(app_config)

            Path("config.json").write_text(
                json.dumps(json.loads(config.model_dump_json()), ensure_ascii=False, sort_keys=True, indent=2)
            )

            app = await app_manager.reload_app(app.id)

        await self.emit_success(
            "app_edit",
            f"App {app.id} edited and reloaded",
            {
                "app_update": await self.app_info(app),
                "new_config": serialise_model(app.arguments, exclude_defaults=True),
                "old_config": old_config,
            },
        )

    async def on_app_schema(self, sid: str, data: dict[str, Any]) -> None:
        app_id = data.get("appId")
        app = await self.get_app_or_send_error("app_edit", sid, app_id)
        if not app:
            return

        await self.emit_success(
            "app_schema",
            f"Got schema for {app.id}",
            {
                "schema": app.arguments.model_json_schema(),
            },
        )

    # ====
    # READ
    # ====

    async def on_apps_config(self, _: str) -> None:
        async with sync_lock:
            await self.emit_success(
                "all_app_configs",
                "All app info retrieved",
                {"apps_update": [await self.app_info(app) for app in app_manager.apps.values()]},
            )

    async def on_app_config(self, sid: str, data: dict[str, Any]) -> None:
        app = await self.get_app_or_send_error("app_config", sid, data.get("appId"))
        if not app:
            return

        await self.emit_success("single_app_config", "App info retrieved", {"app_update": await self.app_info(app)})
