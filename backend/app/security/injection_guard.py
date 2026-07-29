from pydantic import BaseModel, ConfigDict, Field

RISK_PHRASES = [
    "ignore previous instructions",
    "system prompt",
    "developer message",
    "exfiltrate",
    "send secrets",
    "disable safety",
]


class InjectionAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    risky: bool
    matches: list[str] = Field(default_factory=list)


def assess_prompt_injection(text: str) -> InjectionAssessment:
    lowered = text.lower()
    matches = [phrase for phrase in RISK_PHRASES if phrase in lowered]
    return InjectionAssessment(risky=bool(matches), matches=matches)

