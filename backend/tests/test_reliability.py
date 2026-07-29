import asyncio

import pytest

from app.reliability import (
    CircuitBreaker,
    CircuitOpenError,
    InMemoryIdempotencyGuard,
    retry_async,
    run_with_timeout,
)


@pytest.mark.asyncio
async def test_retry_async_recovers_after_transient_failure() -> None:
    calls = 0

    async def operation():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("try again")
        return "ok"

    assert await retry_async(operation, attempts=2, backoff_seconds=0) == "ok"
    assert calls == 2


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_threshold() -> None:
    breaker = CircuitBreaker(failure_threshold=2)

    async def failing():
        raise RuntimeError("down")

    with pytest.raises(RuntimeError):
        await breaker.call(failing)
    with pytest.raises(RuntimeError):
        await breaker.call(failing)
    with pytest.raises(CircuitOpenError):
        await breaker.call(failing)


@pytest.mark.asyncio
async def test_timeout_wrapper_times_out() -> None:
    async def slow():
        await asyncio.sleep(0.1)

    with pytest.raises(asyncio.TimeoutError):
        await run_with_timeout(slow(), seconds=0.001)


@pytest.mark.asyncio
async def test_idempotency_guard_rejects_duplicate() -> None:
    guard = InMemoryIdempotencyGuard()

    assert await guard.reserve("delivery-1") is True
    assert await guard.reserve("delivery-1") is False

