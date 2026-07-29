from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


class CircuitOpenError(RuntimeError):
    pass


class CircuitBreaker:
    def __init__(self, *, failure_threshold: int = 3):
        self.failure_threshold = failure_threshold
        self.failure_count = 0
        self.open = False

    async def call(self, operation: Callable[[], Awaitable[T]]) -> T:
        if self.open:
            raise CircuitOpenError("Circuit breaker is open")
        try:
            result = await operation()
        except Exception:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.open = True
            raise
        self.failure_count = 0
        return result

    def reset(self) -> None:
        self.failure_count = 0
        self.open = False

