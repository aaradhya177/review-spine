import type { FindingRow } from "@/lib/mockData";
import { Severity } from "./StatusBadge";

export function FindingList({ findings }: { findings: FindingRow[] }) {
  if (findings.length === 0) return <div className="empty"><div><strong>No unresolved findings</strong><span>This review has no actionable issues to address.</span></div></div>;
  return <div className="finding-list">{findings.map((finding) => <article className="finding" key={finding.id}>
    <div className="finding-heading"><Severity value={finding.severity} /><strong>{finding.summary}</strong></div>
    <p>{finding.category.replaceAll("-", " ")} identified by {finding.agent} review</p>
    <div className="finding-meta"><span className="mono">{finding.file}:{finding.line}</span><span className="confidence"><span className="confidence-bar"><span style={{ width: `${finding.confidence * 100}%` }} /></span>{Math.round(finding.confidence * 100)}% confidence</span></div>
  </article>)}</div>;
}
