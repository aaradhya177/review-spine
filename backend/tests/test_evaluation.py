from pathlib import Path
from uuid import uuid4

from app.evaluation import RegressionGate, evaluate_findings, load_golden_cases
from app.models.enums import AgentType, FindingSeverity
from app.models.findings import Finding


def test_load_golden_cases() -> None:
    cases = load_golden_cases(Path("backend/tests/fixtures/golden_cases.json"))

    assert cases[0].id == "security-auth-bypass"
    assert cases[0].expected_findings[0].severity == "CRITICAL"


def test_evaluate_findings_matches_expected() -> None:
    case = load_golden_cases(Path("backend/tests/fixtures/golden_cases.json"))[0]
    finding = Finding(
        review_id=uuid4(),
        agent_type=AgentType.SECURITY,
        severity=FindingSeverity.CRITICAL,
        category="auth-bypass",
        summary="Bypass.",
        file_path="auth.py",
        line_start=1,
        confidence=0.9,
        rationale="Missing check.",
    )

    result = evaluate_findings(case, [finding])

    assert result.matched == 1
    assert result.recall == 1.0
    assert RegressionGate(min_recall=1.0).passes(result)


def test_regression_gate_blocks_missed_critical() -> None:
    case = load_golden_cases(Path("backend/tests/fixtures/golden_cases.json"))[0]
    result = evaluate_findings(case, [])

    assert result.missed_criticals == 1
    assert not RegressionGate().passes(result)

