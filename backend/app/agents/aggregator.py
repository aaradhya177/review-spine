from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.agents.contracts import AgentResult
from app.database.repository import ReviewRepository
from app.models.enums import FindingSeverity, ReviewStatus
from app.models.findings import Finding


class AggregationDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_id: UUID
    findings: list[Finding] = Field(default_factory=list)
    overall_confidence: float = Field(ge=0.0, le=1.0)
    route: str
    reason: str
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


@dataclass(frozen=True)
class AggregationPolicy:
    auto_post_confidence_threshold: float = 0.82


class ReviewAggregator:
    def __init__(
        self,
        *,
        policy: AggregationPolicy | None = None,
        repository: ReviewRepository | None = None,
    ):
        self.policy = policy or AggregationPolicy()
        self.repository = repository

    async def aggregate(
        self,
        *,
        review_id: UUID,
        agent_results: list[AgentResult],
    ) -> AggregationDecision:
        findings = self.deduplicate(
            [
                finding
                for result in agent_results
                for finding in result.findings
            ]
        )
        confidence = self.compute_confidence(agent_results=agent_results, findings=findings)
        route, reason, status = self.route(findings=findings, confidence=confidence)
        decision = AggregationDecision(
            review_id=review_id,
            findings=findings,
            overall_confidence=confidence,
            route=route,
            reason=reason,
            metadata={
                "input_agent_count": len(agent_results),
                "finding_count": len(findings),
            },
        )
        if self.repository is not None:
            await self.repository.save_findings(findings)
            await self.repository.update_review_status(
                review_id,
                status,
                overall_confidence=confidence,
                routing_reason=reason,
            )
            if route in {"human_review", "escalate"}:
                await self.repository.create_hitl_review(
                    review_id=review_id,
                    reason=reason,
                )
        return decision

    def deduplicate(self, findings: list[Finding]) -> list[Finding]:
        grouped: dict[tuple[str, int, int | None, str], Finding] = {}
        for finding in findings:
            key = (
                finding.file_path,
                finding.line_start,
                finding.line_end,
                finding.category,
            )
            current = grouped.get(key)
            if current is None or self._is_better(finding, current):
                grouped[key] = finding
        return sorted(
            grouped.values(),
            key=lambda finding: (
                -finding.severity.rank,
                finding.file_path,
                finding.line_start,
                finding.category,
            ),
        )

    def compute_confidence(
        self,
        *,
        agent_results: list[AgentResult],
        findings: list[Finding],
    ) -> float:
        if findings:
            return round(min(finding.confidence for finding in findings), 3)
        if agent_results:
            return round(min(result.confidence for result in agent_results), 3)
        return 1.0

    def route(self, *, findings: list[Finding], confidence: float):
        if any(finding.severity == FindingSeverity.CRITICAL for finding in findings):
            return "escalate", "critical finding requires human escalation", ReviewStatus.ESCALATED
        if confidence < self.policy.auto_post_confidence_threshold:
            return (
                "human_review",
                "overall confidence below auto-post threshold",
                ReviewStatus.AWAITING_HUMAN,
            )
        return "auto_post", "confidence threshold met and no critical findings", ReviewStatus.POSTED

    def _is_better(self, candidate: Finding, current: Finding) -> bool:
        if candidate.confidence != current.confidence:
            return candidate.confidence > current.confidence
        return candidate.severity.rank > current.severity.rank

