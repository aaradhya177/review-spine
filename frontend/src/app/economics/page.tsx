import { getBudget, getEconomics } from "@/lib/api";

export default async function EconomicsPage() {
  const rows = await getEconomics();
  const budget = await getBudget();
  return (
    <>
      <h2 className="page-title">Economics</h2>
      <section className="panel stack" style={{ marginBottom: 16 }}>
        <div className="row">
          <span>Daily budget</span>
          <strong>${budget.dailyCost.toFixed(2)} / ${budget.dailyLimit.toFixed(2)}</strong>
        </div>
      </section>
      <section className="panel">
        <table className="table">
          <thead>
            <tr>
              <th>Agent</th>
              <th>Calls</th>
              <th>Cost</th>
              <th>p95 latency</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.agent}>
                <td>{row.agent}</td>
                <td>{row.calls}</td>
                <td>${row.cost.toFixed(2)}</td>
                <td>{row.p95}ms</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
