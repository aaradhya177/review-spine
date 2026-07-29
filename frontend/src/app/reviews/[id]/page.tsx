import Link from "next/link";
import { ArrowLeft, Check, ChevronRight, Code2, Copy, FileCode2, GitPullRequest, MessageSquareWarning, ShieldCheck, X } from "lucide-react";
import { getReview } from "@/lib/api";
import { ReviewWorkspace } from "@/components/ReviewWorkspace";

export default async function ReviewDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params; const review = await getReview(id);
  return <><div className="page-heading"><div><Link className="muted" href="/reviews"><ArrowLeft className="icon" /> Back to reviews</Link><p className="eyebrow" style={{ marginTop: 18 }}>Review workspace</p><h2 className="page-title">{review.repo} <span className="muted">#{review.pr}</span></h2><p className="page-description">Pull request review · Opened today by Maya Chen</p></div><div className="heading-actions"><button className="button"><Copy className="icon" />Copy link</button><button className="button primary"><GitPullRequest className="icon" />Open on GitHub</button></div></div><ReviewWorkspace review={review} /></>;
}
