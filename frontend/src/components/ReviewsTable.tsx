"use client";
import Link from "next/link";
import { ArrowUpDown, FileCode2, Filter, GitPullRequest, Search, SlidersHorizontal } from "lucide-react";
import { useMemo, useState } from "react";
import type { ReviewRow } from "@/lib/mockData";
import { StatusBadge } from "./StatusBadge";

export function ReviewsTable({ rows }: { rows: ReviewRow[] }) {
  const [query, setQuery] = useState(""); const [status, setStatus] = useState("all");
  const filtered = useMemo(() => rows.filter((r) => `${r.repo} ${r.pr}`.toLowerCase().includes(query.toLowerCase()) && (status === "all" || r.status === status)), [rows, query, status]);
  return <section className="panel"><div className="toolbar"><div className="search"><Search className="icon" aria-hidden="true" /><input className="input" aria-label="Search reviews" placeholder="Search repositories or pull requests" value={query} onChange={(e) => setQuery(e.target.value)} /></div><select className="select" aria-label="Filter by status" value={status} onChange={(e) => setStatus(e.target.value)}><option value="all">All statuses</option><option value="awaiting_human">Needs review</option><option value="posted">Posted</option></select><button className="button" type="button"><Filter className="icon" />Filters</button><button className="button" type="button" aria-label="Sort reviews"><ArrowUpDown className="icon" />Recent</button></div>
    {filtered.length === 0 ? <div className="empty"><div><strong>No reviews match those filters</strong><span>Try a different repository, pull request, or status.</span></div></div> : <div className="table-wrap"><table className="table"><thead><tr><th>Pull request</th><th>Status</th><th>Findings</th><th>Confidence</th><th>Cost</th><th>Updated</th></tr></thead><tbody>{filtered.map((review) => <tr key={review.id}><td><Link className="repo-link" href={`/reviews/${review.id}`}><GitPullRequest className="repo-icon" />{review.repo} <span className="muted">#{review.pr}</span></Link><span className="pr-title">Review completed · {review.findings.length ? "action needed" : "no issues"}</span></td><td><StatusBadge status={review.status} /></td><td><span className={review.findings.length ? "severity high" : "muted"}>{review.findings.length ? `${review.findings.length} open` : "Clear"}</span></td><td>{Math.round(review.confidence * 100)}%</td><td>${review.cost.toFixed(3)}</td><td className="muted">{review.createdAt}</td></tr>)}</tbody></table></div>}
  </section>;
}
