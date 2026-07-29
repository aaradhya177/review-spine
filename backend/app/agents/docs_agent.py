from app.agents.base_agent import BaseReviewAgent
from app.models.enums import AgentType


class DocsReviewAgent(BaseReviewAgent):
    agent_type = AgentType.DOCS
    prompt_name = "docs"

    def concern(self) -> str:
        return "documentation and reader clarity"

