import type { FindingRow } from "@/lib/mockData";

export function FindingList({ findings }: { findings: FindingRow[] }) {
  if (findings.length === 0) {
    return <div className="empty">No actionable findings.</div>;
  }

  return (
    <div className="stack">
      {findings.map((finding) => (
        <article className="finding" key={finding.id}>
          <div>
            <strong>{finding.severity} / {finding.category}</strong>
            <p>{finding.summary}</p>
          </div>
          <div className="finding-meta">
            <span>{finding.agent}</span>
            <span>{finding.file}:{finding.line}</span>
            <span>{Math.round(finding.confidence * 100)}%</span>
          </div>
        </article>
      ))}
    </div>
  );
}

