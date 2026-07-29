import { FindingList } from "@/components/FindingList";
import { StatusBadge } from "@/components/StatusBadge";
import { getReview } from "@/lib/api";

export default async function ReviewDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const review = await getReview(id);
  return (
    <>
      <h2 className="page-title">{review.repo} #{review.pr}</h2>
      <section className="panel stack">
        <div className="row"><span>Status</span><StatusBadge status={review.status} /></div>
        <div className="row"><span>Confidence</span><strong>{Math.round(review.confidence * 100)}%</strong></div>
        <div className="row"><span>Cost</span><strong>${review.cost.toFixed(3)}</strong></div>
        <FindingList findings={review.findings} />
      </section>
    </>
  );
}
