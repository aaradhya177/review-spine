from pydantic import BaseModel, ConfigDict, Field

from app.evaluation.golden_dataset import GoldenCase
from app.models.findings import Finding


class EvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_expected: int = Field(ge=0)
    matched: int = Field(ge=0)
    false_positives: int = Field(ge=0)
    missed_criticals: int = Field(ge=0)

    @property
    def recall(self) -> float:
        if self.total_expected == 0:
            return 1.0
        return self.matched / self.total_expected


def evaluate_findings(case: GoldenCase, produced: list[Finding]) -> EvaluationResult:
    expected_keys = {
        (item.category, item.file_path, item.severity)
        for item in case.expected_findings
    }
    produced_keys = {
        (item.category, item.file_path, item.severity.value)
        for item in produced
    }
    matched = len(expected_keys & produced_keys)
    missed_criticals = sum(
        1
        for expected in case.expected_findings
        if expected.severity == "CRITICAL"
        and (expected.category, expected.file_path, expected.severity) not in produced_keys
    )
    return EvaluationResult(
        total_expected=len(expected_keys),
        matched=matched,
        false_positives=len(produced_keys - expected_keys),
        missed_criticals=missed_criticals,
    )


class RegressionGate:
    def __init__(self, *, min_recall: float = 0.8, allow_missed_criticals: bool = False):
        self.min_recall = min_recall
        self.allow_missed_criticals = allow_missed_criticals

    def passes(self, result: EvaluationResult) -> bool:
        if not self.allow_missed_criticals and result.missed_criticals > 0:
            return False
        return result.recall >= self.min_recall

