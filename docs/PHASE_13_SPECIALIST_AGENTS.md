# Phase 13: Specialist Agents

Phase 13 adds the four concrete specialist agents:

- `SecurityReviewAgent`
- `QualityReviewAgent`
- `TestsReviewAgent`
- `DocsReviewAgent`

Each class is a thin `BaseReviewAgent` subclass that declares:

- `agent_type`
- `prompt_name`
- human-readable concern
- optional post-processing

The security agent currently filters informational findings so it stays focused on exploitable risk.

