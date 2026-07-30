"use client";
import {
  CheckCircle2,
  Clock3,
  GitPullRequest,
  ShieldAlert,
  RefreshCw,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { getReviews } from "@/lib/api";
import type { ReviewRow } from "@/lib/mockData";
import { ReviewsTable } from "@/components/ReviewsTable";

export default function ReviewsPage() {
  const [rows, setRows] = useState<ReviewRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setRows(await getReviews());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load reviews");
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    void load();
  }, [load]);
  const needsReview = rows.filter(
    (review) => review.status === "awaiting_human",
  ).length;
  const openFindings = rows.reduce(
    (sum, review) =>
      sum +
      review.findings.filter((f) => f.state === "open" || !f.state).length,
    0,
  );
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Workspace / Reviews</p>
          <h2 className="page-title">Review desk</h2>
          <p className="page-description">
            A focused queue for code changes that need your judgment.
          </p>
        </div>
        <div className="heading-actions">
          <a className="button" href="/settings">
            <GitPullRequest className="icon" />
            Connect repository
          </a>
        </div>
      </div>
      {loading ? (
        <section className="panel empty">
          <div>
            <strong>Loading reviews</strong>
            <span>Fetching the latest review queue.</span>
          </div>
        </section>
      ) : error ? (
        <section className="panel empty">
          <div>
            <strong>Could not load reviews</strong>
            <span>{error}</span>
            <br />
            <button
              className="button"
              type="button"
              onClick={() => void load()}
            >
              <RefreshCw className="icon" />
              Retry
            </button>
          </div>
        </section>
      ) : (
        <>
          <div className="metric-grid">
            <div className="metric">
              <div className="metric-label">Open reviews</div>
              <div className="metric-value">{rows.length}</div>
              <div className="metric-note">
                <GitPullRequest className="icon" /> All repositories
              </div>
            </div>
            <div className="metric">
              <div className="metric-label">Needs your review</div>
              <div className="metric-value">{needsReview}</div>
              <div className="metric-note">
                <Clock3 className="icon" /> Awaiting a decision
              </div>
            </div>
            <div className="metric">
              <div className="metric-label">Open findings</div>
              <div className="metric-value">{openFindings}</div>
              <div className="metric-note">
                <ShieldAlert className="icon" /> Across current queue
              </div>
            </div>
            <div className="metric">
              <div className="metric-label">Posted today</div>
              <div className="metric-value">
                {rows.filter((review) => review.status === "posted").length}
              </div>
              <div className="metric-note">
                <CheckCircle2 className="icon" /> Review complete
              </div>
            </div>
          </div>
          <ReviewsTable rows={rows} />
        </>
      )}
    </>
  );
}
