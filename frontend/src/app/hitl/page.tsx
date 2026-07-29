import { getReviews } from "@/lib/api";

export default async function HitlPage() {
  const rows = (await getReviews()).filter((review) => review.status === "awaiting_human");
  return (
    <>
      <h2 className="page-title">HITL Queue</h2>
      <section className="panel stack">
        {rows.map((review) => (
          <div className="row" key={review.id}>
            <span>{review.repo} #{review.pr}</span>
            <strong>{Math.round(review.confidence * 100)}%</strong>
          </div>
        ))}
      </section>
    </>
  );
}

