from app.models.findings import Finding


def format_github_review(findings: list[Finding]) -> tuple[str, list[dict]]:
    if not findings:
        return "Review Spine found no actionable findings.", []

    body = "Review Spine found actionable issues worth attention."
    comments = []
    for finding in findings:
        comments.append(
            {
                "path": finding.file_path,
                "line": finding.line_start,
                "body": format_finding_body(finding),
            }
        )
    return body, comments


def format_finding_body(finding: Finding) -> str:
    parts = [
        f"**{finding.severity.value} / {finding.category}**",
        finding.summary,
        "",
        f"Rationale: {finding.rationale}",
        f"Confidence: {finding.confidence:.2f}",
    ]
    if finding.suggestion:
        parts.extend(["", f"Suggestion: {finding.suggestion}"])
    return "\n".join(parts)

