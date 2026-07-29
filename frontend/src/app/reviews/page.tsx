import Link from "next/link";
import { getReviews } from "@/lib/api";

export default async function ReviewsPage() {
  const rows = await getReviews();
  return (
    <>
      <h2 className="page-title">Reviews</h2>
      <section className="panel">
        <table className="table">
          <thead>
            <tr>
              <th>Repository</th>
              <th>PR</th>
              <th>Status</th>
              <th>Confidence</th>
              <th>Cost</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((review) => (
              <tr key={review.id}>
                <td>
                  <Link href={`/reviews/${review.id}`}>{review.repo}</Link>
                </td>
                <td>#{review.pr}</td>
                <td>
                  <span className={`status ${review.status === "awaiting_human" ? "warn" : ""}`}>
                    {review.status}
                  </span>
                </td>
                <td>{Math.round(review.confidence * 100)}%</td>
                <td>${review.cost.toFixed(3)}</td>
                <td>{review.createdAt}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}

