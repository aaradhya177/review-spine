import { CheckCircle2, Clock3, GitPullRequest, ShieldAlert } from "lucide-react";
import { getReviews } from "@/lib/api";
import { ReviewsTable } from "@/components/ReviewsTable";

export default async function ReviewsPage() {
  const rows = await getReviews();
  const needsReview = rows.filter((review) => review.status === "awaiting_human").length;
  const openFindings = rows.reduce((sum, review) => sum + review.findings.length, 0);
  return <>
    <div className="page-heading"><div><p className="eyebrow">Workspace / Reviews</p><h2 className="page-title">Review desk</h2><p className="page-description">A focused queue for code changes that need your judgment.</p></div><div className="heading-actions"><button className="button"><GitPullRequest className="icon" />Connect repository</button></div></div>
    <div className="metric-grid"><div className="metric"><div className="metric-label">Open reviews</div><div className="metric-value">{rows.length}</div><div className="metric-note"><GitPullRequest className="icon" /> All repositories</div></div><div className="metric"><div className="metric-label">Needs your review</div><div className="metric-value">{needsReview}</div><div className="metric-note"><Clock3 className="icon" /> Awaiting a decision</div></div><div className="metric"><div className="metric-label">Open findings</div><div className="metric-value">{openFindings}</div><div className="metric-note"><ShieldAlert className="icon" /> Across current queue</div></div><div className="metric"><div className="metric-label">Posted today</div><div className="metric-value">{rows.filter((review) => review.status === "posted").length}</div><div className="metric-note"><CheckCircle2 className="icon" /> Review complete</div></div></div>
    <ReviewsTable rows={rows} />
  </>;
}
