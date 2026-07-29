from app.agents.base_agent import BaseReviewAgent
from app.models.enums import AgentType, FindingSeverity
from app.models.findings import Finding


class SecurityReviewAgent(BaseReviewAgent):
    agent_type = AgentType.SECURITY
    prompt_name = "security"

    def concern(self) -> str:
        return "exploitable security risk"

    def post_process_findings(self, findings: list[Finding]) -> list[Finding]:
        return [
            finding
            for finding in findings
            if finding.severity != FindingSeverity.INFO
        ]

