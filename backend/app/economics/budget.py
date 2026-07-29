from typing import Protocol


class BudgetExceededError(RuntimeError):
    pass


class CostRepository(Protocol):
    async def get_daily_cost_usd(self) -> float:
        """Return today's recorded LLM spend."""


class InMemoryCostRepository:
    def __init__(self, *, daily_cost_usd: float = 0.0):
        self.daily_cost_usd = daily_cost_usd

    async def get_daily_cost_usd(self) -> float:
        return self.daily_cost_usd


class BudgetGuard:
    def __init__(self, cost_repository: CostRepository, *, daily_limit_usd: float):
        self.cost_repository = cost_repository
        self.daily_limit_usd = daily_limit_usd

    async def check(self) -> None:
        current_cost = await self.cost_repository.get_daily_cost_usd()
        if current_cost >= self.daily_limit_usd:
            raise BudgetExceededError(
                f"Daily LLM budget exceeded: {current_cost:.6f} >= {self.daily_limit_usd:.6f}"
            )

