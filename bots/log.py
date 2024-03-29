import functools
import logging
import time
from asyncio import Queue
from typing import Any, Callable, TypedDict

from bots.config import config
from bots.utils.misc import get_arg_value


class LogEntry(TypedDict):
    text: str
    status: str
    timestamp: int


runtime_logs: list[LogEntry] = []

logger = logging.getLogger("bot_manager")
logger.setLevel(config.local_log_level)


class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("/list") == -1 and record.getMessage().find("/log") == -1


# Filter out /endpoint
logging.getLogger("uvicorn.access").addFilter(EndpointFilter())


class SocketLogHandler(logging.Handler):
    def __init__(self, level: int = logging.NOTSET) -> None:
        super().__init__(level)

        self.queue = Queue[dict[str, Any]]()

    def emit(self, record: logging.LogRecord) -> None:
        status = (
            "error"
            if record.levelno >= logging.ERROR
            else ("warning" if record.levelno >= logging.WARNING else "success")
        )
        self.queue.put_nowait(
            {
                "status": status,
                "message": self.format(record),
                "data": {
                    "timestamp": int(record.created),
                },
            }
        )


def log(arg_names: list[str] = [], ignore_incoming: bool = False) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator_log(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
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

                if entry["status"] != "success" or not ignore_incoming:
                    logger.info(entry["text"])
                    runtime_logs.append(entry)

            return response

        return wrapper

    return decorator_log
