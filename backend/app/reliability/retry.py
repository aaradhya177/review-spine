import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


async def retry_async(
    operation: Callable[[], Awaitable[T]],
    *,
    attempts: int = 3,
    backoff_seconds: float = 0.01,
) -> T:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return await operation()
        except Exception as exc:
            last_error = exc
            if attempt < attempts:
                await asyncio.sleep(backoff_seconds * attempt)
    assert last_error is not None
    raise last_error

