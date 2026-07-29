from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.economics.cost_repository import AgentCostSummary

router = APIRouter(prefix="/economics", tags=["economics"])


class InMemoryEconomicsService:
    def __init__(self, summaries: list[AgentCostSummary] | None = None, daily_cost: float = 0.0):
        self.summaries = summaries or []
        self.daily_cost = daily_cost

    async def cost_by_agent(self) -> list[AgentCostSummary]:
        return self.summaries

    async def daily_budget_state(self) -> dict:
        return {"daily_cost_usd": self.daily_cost}


_fallback_service = InMemoryEconomicsService()


def get_economics_service(request: Request):
    return getattr(request.app.state, "economics_service", _fallback_service)


@router.get("/agents", response_model=list[AgentCostSummary])
async def agents(
    service: Annotated[InMemoryEconomicsService, Depends(get_economics_service)],
) -> list[AgentCostSummary]:
    return await service.cost_by_agent()


@router.get("/budget")
async def budget(
    service: Annotated[InMemoryEconomicsService, Depends(get_economics_service)],
) -> dict:
    return await service.daily_budget_state()

