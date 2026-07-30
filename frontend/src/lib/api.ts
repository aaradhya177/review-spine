import type {
  ReviewRow,
  FindingRow,
  SettingsData,
  TraceEvent,
} from "./mockData";

type BackendFinding = Omit<FindingRow, "confidence"> & { confidence: number };
type BackendReview = Omit<
  ReviewRow,
  "createdAt" | "findings" | "decisionHistory" | "comments"
> & {
  created_at: string;
  findings: BackendFinding[];
  decision_history: Record<string, string>[];
  comments: Record<string, string>[];
};

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function baseUrl() {
  return typeof window === "undefined"
    ? (process.env.BACKEND_URL ?? "http://localhost:8000")
    : "/api/backend";
}

export async function apiFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${baseUrl()}${path}`, {
    ...init,
    cache: "no-store",
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      message = body.detail ?? message;
    } catch {}
    throw new ApiError(response.status, message);
  }
  return response.json() as Promise<T>;
}

function mapFinding(finding: BackendFinding): FindingRow {
  return { ...finding, severity: finding.severity.toLowerCase() };
}
function mapReview(review: BackendReview): ReviewRow {
  return {
    ...review,
    createdAt: review.created_at,
    findings: review.findings.map(mapFinding),
    decisionHistory: review.decision_history,
    comments: review.comments,
  };
}

export async function getReviews(): Promise<ReviewRow[]> {
  const rows = await apiFetch<BackendReview[]>("/reviews");
  return rows.map(mapReview);
}
export async function getReview(id: string): Promise<ReviewRow> {
  return mapReview(await apiFetch<BackendReview>(`/reviews/${id}`));
}
export async function resolveFinding(
  reviewId: string,
  findingId: string,
): Promise<ReviewRow> {
  return mapReview(
    await apiFetch<BackendReview>(
      `/reviews/${reviewId}/findings/${findingId}/resolve`,
      { method: "POST" },
    ),
  );
}
export async function dismissFinding(
  reviewId: string,
  findingId: string,
  decidedBy: string,
  reason: string,
): Promise<ReviewRow> {
  return mapReview(
    await apiFetch<BackendReview>(
      `/reviews/${reviewId}/findings/${findingId}/dismiss`,
      {
        method: "POST",
        body: JSON.stringify({ decided_by: decidedBy, reason }),
      },
    ),
  );
}
export async function decideReview(
  reviewId: string,
  decidedBy: string,
  decision: "approved" | "dismissed" | "rejected" | "escalated",
  reason: string = decision,
): Promise<ReviewRow> {
  return mapReview(
    await apiFetch<BackendReview>(`/reviews/${reviewId}/decision`, {
      method: "POST",
      body: JSON.stringify({ decided_by: decidedBy, decision, reason }),
    }),
  );
}
export async function addComment(
  reviewId: string,
  body: string,
  findingId?: string,
): Promise<ReviewRow> {
  return mapReview(
    await apiFetch<BackendReview>(`/reviews/${reviewId}/comments`, {
      method: "POST",
      body: JSON.stringify({
        author: "local.user",
        body,
        finding_id: findingId,
      }),
    }),
  );
}
export async function getTrace(reviewId?: string): Promise<TraceEvent[]> {
  const rows = await apiFetch<
    { event: string; status: string; review_id?: string }[]
  >(reviewId ? `/reviews/${reviewId}/trace` : "/reviews/review-1/trace");
  return rows.map((row, index) => ({
    id: `${row.event}-${index}`,
    event: row.event,
    status: row.status,
    reviewId: row.review_id ?? "",
  }));
}
export async function getEconomics() {
  return apiFetch<
    {
      agent: string;
      llm_calls: number;
      cost_usd: number;
      p95_latency_ms: number | null;
    }[]
  >("/economics/agents");
}
export async function getBudget() {
  return apiFetch<{ daily_cost_usd: number }>("/economics/budget");
}
export async function getSettings(): Promise<SettingsData> {
  return apiFetch<SettingsData>("/reviews/settings/current");
}
export async function saveSettings(
  settings: SettingsData,
): Promise<SettingsData> {
  return apiFetch<SettingsData>("/reviews/settings/current", {
    method: "PUT",
    body: JSON.stringify(settings),
  });
}
