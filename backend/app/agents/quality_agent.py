from app.agents.base_agent import BaseReviewAgent
from app.models.enums import AgentType


class QualityReviewAgent(BaseReviewAgent):
    agent_type = AgentType.QUALITY
    prompt_name = "quality"

    def concern(self) -> str:
        return "correctness and maintainability"

