"use client";
import Link from "next/link";
import { ArrowLeft, Copy, GitPullRequest, RefreshCw } from "lucide-react";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { getReview } from "@/lib/api";
import type { ReviewRow } from "@/lib/mockData";
import { ReviewWorkspace } from "@/components/ReviewWorkspace";

export default function ReviewDetail() {
  const { id } = useParams<{ id: string }>();
  const [review, setReview] = useState<ReviewRow | null>(null);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => {
    setError(null);
    try {
      setReview(await getReview(id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load review");
    }
  }, [id]);
  useEffect(() => {
    void load();
  }, [load]);
  const copyLink = async () => {
    await navigator.clipboard.writeText(window.location.href);
    window.dispatchEvent(
      new CustomEvent("review-toast", { detail: "Review link copied" }),
    );
  };
  if (error)
    return (
      <section className="panel empty">
        <div>
          <strong>Could not load this review</strong>
          <span>{error}</span>
          <br />
          <button className="button" type="button" onClick={() => void load()}>
            <RefreshCw className="icon" />
            Retry
          </button>
        </div>
      </section>
    );
  if (!review)
    return (
      <section className="panel empty">
        <div>
          <strong>Loading review</strong>
          <span>Fetching review details and findings.</span>
        </div>
      </section>
    );
  return (
    <>
      <div className="page-heading">
        <div>
          <Link className="muted inline-link" href="/reviews">
            <ArrowLeft className="icon" /> Back to reviews
          </Link>
          <p className="eyebrow" style={{ marginTop: 18 }}>
            Review workspace
          </p>
          <h2 className="page-title">
            {review.repo} <span className="muted">#{review.pr}</span>
          </h2>
          <p className="page-description">
            {review.title} · Opened by {review.author}
          </p>
        </div>
        <div className="heading-actions">
          <button
            className="button"
            type="button"
            onClick={() => void copyLink()}
          >
            <Copy className="icon" />
            Copy link
          </button>
          <a
            className="button primary"
            href={`https://github.com/${review.repo}/pull/${review.pr}`}
            target="_blank"
            rel="noreferrer"
          >
            <GitPullRequest className="icon" />
            Open on GitHub
          </a>
        </div>
      </div>
      <ReviewWorkspace review={review} onUpdated={setReview} />
    </>
  );
}
