export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`status ${status === "awaiting_human" ? "warn" : ""}`}>
      {status}
    </span>
  );
}

