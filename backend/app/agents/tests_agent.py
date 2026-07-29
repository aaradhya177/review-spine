from app.agents.base_agent import BaseReviewAgent
from app.models.enums import AgentType


class TestsReviewAgent(BaseReviewAgent):
    __test__ = False

    agent_type = AgentType.TESTS
    prompt_name = "tests"

    def concern(self) -> str:
        return "test coverage and regression risk"
