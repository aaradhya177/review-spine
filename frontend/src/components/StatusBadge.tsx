export function StatusBadge({ status }: { status: string }) {
  const normalized = status.toLowerCase();
  const tone = normalized.includes("await") ? "warn" : normalized.includes("error") ? "danger" : normalized === "posted" ? "" : "neutral";
  const label = status.replaceAll("_", " ");
  return <span className={`status ${tone}`}><span className="status-dot" />{label}</span>;
}

export function Severity({ value }: { value: string }) {
  const tone = value.toLowerCase();
  return <span className={`severity ${tone}`}><span className="severity-dot" />{tone}</span>;
}
