export type ReviewRow = {
  id: string;
  repo: string;
  pr: number;
  status: string;
  confidence: number;
  cost: number;
  createdAt: string;
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
  },
  {
    id: "review-2",
    repo: "acme/api",
    pr: 108,
    status: "posted",
    confidence: 0.91,
    cost: 0.024,
    createdAt: "2026-07-30 08:44",
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

