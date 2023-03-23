from socketio import AsyncNamespace

from bots.log import logger


from socketio import AsyncNamespace


class Namespace(AsyncNamespace):
    def __init__(self, namespace=None):
        super().__init__(namespace or getattr(self, "namespace"))

    async def on_connect(self, sid: str, environ: dict) -> None:
        logger.info(f"{self.namespace} client connected: {sid}")

    async def on_disconnect(self, sid: str) -> None:
        logger.info(f"{self.namespace} client disconnected: {sid}")

    async def trigger_event(self, event, *args):
        logger.info(f"Request received for {event} with args: {args[0]}")
        return await super().trigger_event(event, *args)

    async def emit_default(
        self, event, status: str, message: str, data: list | dict | None = None, sid: str | None = None
    ):
        await self.emit(
            event,
            {
                "status": status,
                "message": message if message else "An error occurred" if status == "error" else None,
                "data": data,
            },
            room=sid,
        )

    async def emit_success(self, event: str, message: str, data: list | dict | None = None, sid: str | None = None):
        await self.emit_default(event, "success", message, data, sid)

    async def emit_error(self, event: str, message: str, data: list | dict | None = None, sid: str | None = None):
        await self.emit_default(event, "error", message, data, sid)

    async def emit_warning(self, event: str, message: str, data: list | dict | None = None, sid: str | None = None):
        await self.emit_default(event, "warning", message, data, sid)
