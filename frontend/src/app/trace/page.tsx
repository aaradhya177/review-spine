import { getTrace } from "@/lib/api";

export default async function TracePage() {
  const events = await getTrace();
  return (
    <>
      <h2 className="page-title">Trace Viewer</h2>
      <section className="panel stack">
        {events.map((event, index) => (
          <div className="row" key={event}>
            <span>{index + 1}</span>
            <strong>{event}</strong>
          </div>
        ))}
      </section>
    </>
  );
}

