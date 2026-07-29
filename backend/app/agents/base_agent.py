import asyncio
from abc import ABC, abstractmethod
from typing import Any

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.contracts import AgentInput, AgentResult
from app.memory.context_retriever import ContextRetriever, RetrievedContext
from app.models.enums import AgentType
from app.models.findings import Evidence, Finding
from app.observability.events import AgentEvent, emit_agent_event
from app.prompts import PromptRegistry
from app.tools import LLMClient, LLMRequest, ModelRouter


class BaseReviewAgent(ABC):
    agent_type: AgentType
    prompt_name: str

    def __init__(
        self,
        *,
        retriever: ContextRetriever,
        prompt_registry: PromptRegistry,
        llm_client: LLMClient,
        model_router: ModelRouter,
        event_session: AsyncSession | None = None,
        prompt_version: str = "v1",
        timeout_seconds: float = 30.0,
        max_attempts: int = 1,
    ):
        self.retriever = retriever
        self.prompt_registry = prompt_registry
        self.llm_client = llm_client
        self.model_router = model_router
        self.event_session = event_session
        self.prompt_version = prompt_version
        self.timeout_seconds = timeout_seconds
        self.max_attempts = max(1, max_attempts)

    async def run(self, input: AgentInput) -> AgentResult:
        await self._emit(input, "span.start")
        evidence: list[RetrievedContext] = []
        try:
            evidence = await self.retriever.retrieve(
                repo=input.repo_full_name,
                diff_text=input.diff_text,
                changed_files=input.changed_files,
                agent_type=self.agent_type.value,
            )
            prompt = self._build_prompt(input, evidence)
            response_content = await self._call_llm_with_retries(input, prompt)
            result = self._parse_response(input, response_content, evidence)
        except Exception as exc:
            await self._emit(input, "span.end", outcome="failed", payload={"error": str(exc)})
            return AgentResult(
                agent_type=self.agent_type.value,
                confidence=0.0,
                evidence=evidence,
                errors=[str(exc)],
                metadata={"prompt_version": self.prompt_id},
            )

        await self._emit(
            input,
            "span.end",
            outcome="completed",
            confidence=result.confidence,
            payload={"finding_count": len(result.findings)},
        )
        return result

    @property
    def prompt_id(self) -> str:
        return f"{self.prompt_name}@{self.prompt_version}"

    def _build_prompt(self, input: AgentInput, evidence: list[RetrievedContext]) -> str:
        template = self.prompt_registry.get(self.prompt_name, self.prompt_version)
        context = "\n\n".join(
            f"[{item.rank}] {item.path}\n{item.content}" for item in evidence
        )
        return template.render(diff=input.diff_text, context=context)

    async def _call_llm_with_retries(
        self,
        input: AgentInput,
        prompt: str,
    ) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                response = await asyncio.wait_for(
                    self.llm_client.complete_structured(
                        LLMRequest(
                            review_id=input.review_id,
                            agent=self.agent_type.value,
                            model=self.model_router.choose_review_model(self.agent_type),
                            prompt=prompt,
                            prompt_version=self.prompt_id,
                            response_schema="AgentResult",
                        )
                    ),
                    timeout=self.timeout_seconds,
                )
                return response.content
            except Exception as exc:
                last_error = exc
                await self._emit(
                    input,
                    "retry",
                    outcome="failed",
                    payload={"attempt": attempt, "error": str(exc)},
                )
        assert last_error is not None
        raise last_error

    def _parse_response(
        self,
        input: AgentInput,
        response_content: dict[str, Any],
        evidence: list[RetrievedContext],
    ) -> AgentResult:
        raw_findings = response_content.get("findings", [])
        findings: list[Finding] = []
        errors: list[str] = []
        for raw in raw_findings:
            try:
                payload = {
                    **raw,
                    "review_id": input.review_id,
                    "agent_type": self.agent_type,
                    "evidence": raw.get("evidence") or self._evidence_for_finding(evidence),
                }
                findings.append(Finding.model_validate(payload))
            except ValidationError as exc:
                errors.append(str(exc))
        confidence = response_content.get("confidence")
        if confidence is None:
            confidence = min((finding.confidence for finding in findings), default=1.0)
        return AgentResult(
            agent_type=self.agent_type.value,
            findings=self.post_process_findings(findings),
            confidence=confidence,
            evidence=evidence,
            errors=errors,
            metadata={
                "prompt_version": self.prompt_id,
                "model": self.model_router.choose_review_model(self.agent_type),
                "raw_finding_count": len(raw_findings),
            },
        )

    def _evidence_for_finding(self, evidence: list[RetrievedContext]) -> list[Evidence]:
        return [
            Evidence(
                source="retrieval",
                path=item.path,
                symbol=item.symbol,
                excerpt=item.content[:500],
                rank=item.rank,
                metadata={"method": item.method, "score": item.score},
            )
            for item in evidence[:3]
        ]

    async def _emit(
        self,
        input: AgentInput,
        event_type: str,
        *,
        outcome: str | None = None,
        confidence: float | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        if self.event_session is None:
            return
        await emit_agent_event(
            self.event_session,
            AgentEvent(
                review_id=input.review_id,
                agent=self.agent_type.value,
                event_type=event_type,
                outcome=outcome,
                confidence=confidence,
                payload=payload or {},
            ),
        )

    def post_process_findings(self, findings: list[Finding]) -> list[Finding]:
        return findings

    @abstractmethod
    def concern(self) -> str:
        """Return a short human-readable concern name."""

