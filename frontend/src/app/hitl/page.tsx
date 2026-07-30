"use client";
import Link from "next/link";
import { CheckCircle2, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { getReviews } from "@/lib/api";
import type { ReviewRow } from "@/lib/mockData";
import { HitlActions } from "@/components/HitlActions";

export default function HitlPage() {
  const [rows, setRows] = useState<ReviewRow[]>([]); const [loading, setLoading] = useState(true); const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => { setLoading(true); setError(null); try { setRows((await getReviews()).filter((review) => review.status === "awaiting_human")); } catch (err) { setError(err instanceof Error ? err.message : "Unable to load review queue"); } finally { setLoading(false); } }, []); useEffect(() => { void load(); }, [load]);
  return <><div className="page-heading"><div><p className="eyebrow">Workspace / Needs review</p><h2 className="page-title">Human review queue</h2><p className="page-description">Decisions that need a developer before the review can move forward.</p></div></div>{loading ? <section className="panel empty"><div><strong>Loading queue</strong><span>Checking for pending decisions.</span></div></section> : error ? <section className="panel empty"><div><strong>Could not load queue</strong><span>{error}</span><br /><button className="button" type="button" onClick={() => void load()}><RefreshCw className="icon" />Retry</button></div></section> : rows.length === 0 ? <section className="panel empty"><div><CheckCircle2 className="icon" /><strong>Queue is clear</strong><span>There are no reviews waiting for your decision.</span></div></section> : <section className="panel stack">{rows.map((review) => <article key={review.id}><div className="row"><div><Link className="repo-link" href={`/reviews/${review.id}`}>{review.repo} #{review.pr}</Link><p className="page-description">{review.title} · {review.findings.length} findings</p></div><strong>{Math.round(review.confidence * 100)}%</strong></div><HitlActions review={review} onComplete={(updated) => setRows((current) => current.filter((item) => item.id !== updated.id))} /></article>)}</section>}</>;
}
