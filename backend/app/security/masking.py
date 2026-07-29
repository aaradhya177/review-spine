import re
from typing import Any

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{8,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]+"),
    re.compile(r"(?i)(password|secret|token|api_key)=([^&\s]+)"),
]


def mask_secrets(value: Any) -> Any:
    if isinstance(value, str):
        masked = value
        for pattern in SECRET_PATTERNS:
            if pattern.groups >= 2:
                masked = pattern.sub(lambda match: f"{match.group(1)}=***", masked)
            else:
                masked = pattern.sub("***", masked)
        return masked
    if isinstance(value, list):
        return [mask_secrets(item) for item in value]
    if isinstance(value, dict):
        return {key: mask_secrets(item) for key, item in value.items()}
    return value

