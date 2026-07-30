"use client";
import Link from "next/link";
import { ArrowUpDown, Filter, GitPullRequest, Search, X } from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";
import type { ReviewRow } from "@/lib/mockData";
import { StatusBadge } from "./StatusBadge";

type Sort = "newest" | "oldest" | "severity" | "confidence" | "findings";

export function ReviewsTable({ rows }: { rows: ReviewRow[] }) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const [filtersOpen, setFiltersOpen] = useState(false);
  const query = params.get("q") ?? "";
  const status = params.get("status") ?? "all";
  const severity = params.get("severity") ?? "all";
  const repo = params.get("repo") ?? "all";
  const author = params.get("author") ?? "all";
  const sort = (params.get("sort") as Sort | null) ?? "newest";
  const update = (key: string, value: string) => {
    const next = new URLSearchParams(params.toString());
    if (!value || value === "all") next.delete(key);
    else next.set(key, value);
    router.replace(`${pathname}${next.size ? `?${next}` : ""}`);
  };
  const clear = () => router.replace(pathname);
  const filtered = useMemo(() => {
    const result = rows.filter((r) => {
      const text = `${r.repo} ${r.pr} ${r.author} ${r.title}`.toLowerCase();
      const matchesSearch = text.includes(query.toLowerCase());
      const matchesSeverity =
        severity === "all" ||
        r.findings.some(
          (finding) => finding.severity.toLowerCase() === severity,
        );
      return (
        matchesSearch &&
        (status === "all" || r.status === status) &&
        matchesSeverity &&
        (repo === "all" || r.repo === repo) &&
        (author === "all" || r.author === author)
      );
    });
    return [...result].sort((a, b) =>
      sort === "oldest"
        ? a.createdAt.localeCompare(b.createdAt)
        : sort === "severity"
          ? b.findings.length - a.findings.length
          : sort === "confidence"
            ? b.confidence - a.confidence
            : sort === "findings"
              ? b.findings.length - a.findings.length
              : b.createdAt.localeCompare(a.createdAt),
    );
  }, [rows, query, status, severity, repo, author, sort]);
  const hasFilters = Boolean(
    query ||
    status !== "all" ||
    severity !== "all" ||
    repo !== "all" ||
    author !== "all",
  );
  return (
    <section className="panel">
      <div className="toolbar">
        <div className="search">
          <Search className="icon" aria-hidden="true" />
          <input
            className="input"
            aria-label="Search reviews"
            placeholder="Search repositories, PRs, authors"
            value={query}
            onChange={(e) => update("q", e.target.value)}
          />
        </div>
        <select
          className="select"
          aria-label="Filter by status"
          value={status}
          onChange={(e) => update("status", e.target.value)}
        >
          <option value="all">All statuses</option>
          <option value="awaiting_human">Needs review</option>
          <option value="posted">Posted</option>
        </select>
        <button
          className={`button ${filtersOpen ? "primary" : ""}`}
          type="button"
          aria-expanded={filtersOpen}
          onClick={() => setFiltersOpen(!filtersOpen)}
        >
          <Filter className="icon" />
          Filters
        </button>
        <select
          className="select"
          aria-label="Sort reviews"
          value={sort}
          onChange={(e) => update("sort", e.target.value)}
        >
          <option value="newest">Newest</option>
          <option value="oldest">Oldest</option>
          <option value="severity">Severity</option>
          <option value="confidence">Confidence</option>
          <option value="findings">Findings</option>
        </select>
      </div>
      {filtersOpen && (
        <div className="toolbar" role="region" aria-label="Review filters">
          <select
            className="select"
            aria-label="Filter by severity"
            value={severity}
            onChange={(e) => update("severity", e.target.value)}
          >
            <option value="all">All severities</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <select
            className="select"
            aria-label="Filter by repository"
            value={repo}
            onChange={(e) => update("repo", e.target.value)}
          >
            <option value="all">All repositories</option>
            {Array.from(new Set(rows.map((r) => r.repo))).map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
          <select
            className="select"
            aria-label="Filter by author"
            value={author}
            onChange={(e) => update("author", e.target.value)}
          >
            <option value="all">All authors</option>
            {Array.from(new Set(rows.map((r) => r.author))).map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
          {hasFilters && (
            <button className="button ghost" type="button" onClick={clear}>
              <X className="icon" />
              Clear filters
            </button>
          )}
        </div>
      )}
      {hasFilters && (
        <div className="active-filters" aria-label="Active filters">
          <span>{filtered.length} matching reviews</span>
          <button className="button ghost" type="button" onClick={clear}>
            Clear all
          </button>
        </div>
      )}
      {filtered.length === 0 ? (
        <div className="empty">
          <div>
            <strong>No reviews match those filters</strong>
            <span>
              Try a different repository, pull request, author, or status.
            </span>
            <br />
            <button className="button" type="button" onClick={clear}>
              Reset filters
            </button>
          </div>
        </div>
      ) : (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Pull request</th>
                <th>Status</th>
                <th>Findings</th>
                <th>Confidence</th>
                <th>Cost</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((review) => (
                <tr key={review.id}>
                  <td>
                    <Link className="repo-link" href={`/reviews/${review.id}`}>
                      <GitPullRequest className="repo-icon" />
                      {review.repo} <span className="muted">#{review.pr}</span>
                    </Link>
                    <span className="pr-title">
                      {review.title} · {review.author}
                    </span>
                  </td>
                  <td>
                    <StatusBadge status={review.status} />
                  </td>
                  <td>
                    <span
                      className={
                        review.findings.length ? "severity high" : "muted"
                      }
                    >
                      {review.findings.length
                        ? `${review.findings.length} open`
                        : "Clear"}
                    </span>
                  </td>
                  <td>{Math.round(review.confidence * 100)}%</td>
                  <td>${review.cost.toFixed(3)}</td>
                  <td className="muted">{review.createdAt}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
