# Phase 22: Evaluation Harness

Phase 22 adds a local evaluation harness.

## Golden Dataset

`GoldenCase` stores:

- case id
- diff text
- expected findings

## Metrics

`evaluate_findings` reports:

- total expected findings
- matched findings
- false positives
- missed criticals
- recall

## Regression Gate

`RegressionGate` blocks missed critical findings and enforces minimum recall.

