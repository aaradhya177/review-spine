import asyncio
from collections.abc import Awaitable
from typing import TypeVar

T = TypeVar("T")


async def run_with_timeout(awaitable: Awaitable[T], *, seconds: float) -> T:
    return await asyncio.wait_for(awaitable, timeout=seconds)

