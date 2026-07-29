import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class GoldenFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str
    file_path: str
    severity: str


class GoldenCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    diff: str
    expected_findings: list[GoldenFinding] = Field(default_factory=list)


def load_golden_cases(path: Path) -> list[GoldenCase]:
    return [GoldenCase.model_validate(item) for item in json.loads(path.read_text())]

