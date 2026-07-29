export type ReviewRow = {
  id: string;
  repo: string;
  pr: number;
  status: string;
  confidence: number;
  cost: number;
  createdAt: string;
  findings: FindingRow[];
};

export type FindingRow = {
  id: string;
  agent: string;
  severity: string;
  category: string;
  file: string;
  line: number;
  summary: string;
  confidence: number;
};

export const reviews: ReviewRow[] = [
  {
    id: "review-1",
    repo: "acme/shop",
    pr: 42,
    status: "awaiting_human",
    confidence: 0.61,
    cost: 0.038,
    createdAt: "2026-07-30 09:20",
    findings: [
      {
        id: "finding-1",
        agent: "security",
        severity: "HIGH",
        category: "auth-bypass",
        file: "backend/app/auth.py",
        line: 88,
        summary: "Role check is skipped for token refresh.",
        confidence: 0.76,
      },
      {
        id: "finding-2",
        agent: "tests",
        severity: "MEDIUM",
        category: "missing-test",
        file: "backend/tests/test_auth.py",
        line: 12,
        summary: "No regression test covers refresh denial.",
        confidence: 0.68,
      },
    ],
  },
  {
    id: "review-2",
    repo: "acme/api",
    pr: 108,
    status: "posted",
    confidence: 0.91,
    cost: 0.024,
    createdAt: "2026-07-30 08:44",
    findings: [],
  },
];

export const traceEvents = [
  "webhook.received",
  "queue.enqueued",
  "orchestrator.span.start",
  "security.llm.call",
  "quality.llm.call",
  "aggregator.decision",
];

export const economics = [
  { agent: "security", calls: 12, cost: 0.44, p95: 1320 },
  { agent: "quality", calls: 12, cost: 0.31, p95: 980 },
  { agent: "tests", calls: 8, cost: 0.18, p95: 760 },
];

export const budget = {
  dailyCost: 0.93,
  dailyLimit: 25,
};
