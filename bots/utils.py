import asyncio
import functools
import inspect
import logging
import re
from typing import AsyncIterable, AsyncIterator, TypeVar

logger = logging.getLogger("bot_manager")


def get_arg_value(arg_name, func, args, kwargs):
    if arg_name in kwargs:
        return kwargs[arg_name]

    # Get the argument index from the function signature
    signature = inspect.signature(func)
    index = list(signature.parameters.keys()).index(arg_name)

    if index < len(args):
        return args[index]
    else:
        return None  # The argument was not provided


T = TypeVar("T")


async def async_throttled_iterator(async_iterator: AsyncIterable[T], delay: float | int) -> AsyncIterator[T | None]:
    last_item: T | None = None
    item_available = asyncio.Event()
    iterator_exhausted = asyncio.Event()

    async def consume_items():
        nonlocal last_item
        async for item in async_iterator:
            last_item = item
            item_available.set()
        iterator_exhausted.set()

    async def produce_items():
        while not iterator_exhausted.is_set() or item_available.is_set():
            await item_available.wait()
            item_available.clear()
            yield last_item
            if not iterator_exhausted.is_set():
                await asyncio.sleep(delay)

    async def cleanup(task):
        try:
            await task
        except asyncio.CancelledError:
            pass

    consume_task = asyncio.create_task(consume_items())
    try:
        async for item in produce_items():
            yield item
    finally:
        consume_task.cancel()
        await cleanup(consume_task)


def stabelise_string(text: str, entity_type: str = "") -> str:
    """Helper function to escape telegram markup symbols."""
    if entity_type in ["pre", "code"]:
        escape_chars = r"\`"
    elif entity_type == "text_link":
        escape_chars = r"\)"
    elif entity_type == "all":
        escape_chars = r"\_*[]()~`>#+-=|{}.!"
    else:
        escape_chars = r"\[]()~>#+-=|{}.!"

    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)


def safe_error(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except (Exception, BaseException) as error:
            logger.error(error)
            return {"status": "error", "message": "An error occurred"}

    return wrapper
