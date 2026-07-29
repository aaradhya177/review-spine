from app.config import Settings
from app.models.enums import AgentType


class ModelRouter:
    def __init__(self, settings: Settings):
        self.settings = settings

    def choose_review_model(self, agent_type: AgentType) -> str:
        if self.settings.default_review_model:
            return self.settings.default_review_model
        return {
            AgentType.SECURITY: "review-security-local",
            AgentType.QUALITY: "review-quality-local",
            AgentType.TESTS: "review-tests-local",
            AgentType.DOCS: "review-docs-local",
            AgentType.AGGREGATOR: "review-aggregator-local",
        }[agent_type]

