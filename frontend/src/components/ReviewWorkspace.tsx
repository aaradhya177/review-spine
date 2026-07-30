"use client";
import {
  Check,
  FileCode2,
  MessageSquareWarning,
  ShieldCheck,
  X,
  RefreshCw,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  addComment,
  decideReview,
  dismissFinding,
  resolveFinding,
} from "@/lib/api";
import type { ReviewRow } from "@/lib/mockData";
import { Severity, StatusBadge } from "./StatusBadge";

const codeLines = [
  ["84", "84", "  const session = await sessions.get(token);"],
  ["85", "85", "  if (!session) return unauthorized();"],
  ["86", "86", ""],
  ["87", "87", "+ const user = await users.find(session.userId);"],
  ["88", "88", "+ return issueToken({ user, refresh: true });"],
  ["89", "89", "  return issueToken({ user, refresh: true });"],
];

function ActionDialog({
  title,
  description,
  requireReason,
  onClose,
  onSubmit,
}: {
  title: string;
  description: string;
  requireReason?: boolean;
  onClose: () => void;
  onSubmit: (reason: string) => Promise<void>;
}) {
  const [reason, setReason] = useState("");
  const [saving, setSaving] = useState(false);
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const element = dialog.current;
    element?.showModal();
    return () => element?.close();
  }, []);
  return (
    <dialog className="dialog" ref={dialog} onCancel={onClose}>
      <form
        method="dialog"
        onSubmit={async (event) => {
          event.preventDefault();
          if (requireReason && !reason.trim()) return;
          setSaving(true);
          try {
            await onSubmit(reason);
            onClose();
          } finally {
            setSaving(false);
          }
        }}
      >
        <div className="dialog-header">
          <div>
            <h3>{title}</h3>
            <p>{description}</p>
          </div>
          <button
            className="button ghost"
            type="button"
            aria-label="Close dialog"
            onClick={onClose}
          >
            <X className="icon" />
          </button>
        </div>
        <label className="field-label">
          {requireReason ? "Reason" : "Comment"}
          <textarea
            className="textarea"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            required={requireReason}
            placeholder={
              requireReason ? "Explain this decision" : "Write a comment"
            }
            autoFocus
          />
        </label>
        <div className="dialog-actions">
          <button className="button" type="button" onClick={onClose}>
            Cancel
          </button>
          <button
            className="button primary"
            type="submit"
            disabled={saving || (requireReason && !reason.trim())}
          >
            {saving ? "Saving…" : "Confirm"}
          </button>
        </div>
      </form>
    </dialog>
  );
}

export function ReviewWorkspace({
  review,
  onUpdated,
}: {
  review: ReviewRow;
  onUpdated: (review: ReviewRow) => void;
}) {
  const [selectedId, setSelectedId] = useState(
    review.findings.find(
      (finding) => finding.state === "open" || !finding.state,
    )?.id,
  );
  const [tab, setTab] = useState<"changes" | "summary" | "checks">("changes");
  const [dialog, setDialog] = useState<
    "approve" | "dismiss-all" | "dismiss" | "comment" | null
  >(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [files, setFiles] = useState<string[]>([]);
  const [currentFile, setCurrentFile] = useState(review.findings[0]?.file ?? "");
  const selected = review.findings.find((finding) => finding.id === selectedId);
  const openFindings = review.findings.filter(
    (finding) => finding.state === "open" || !finding.state,
  );
  const changedFiles = useMemo(
    () =>
      Array.from(new Set(review.findings.map((finding) => finding.file))).concat(
        review.findings.length ? ["backend/app/models/session.py"] : [],
      ),
    [review.findings],
  );
  useEffect(() => {
    setFiles(changedFiles);
  }, [changedFiles]);
  const run = async (operation: () => Promise<ReviewRow>) => {
    setBusy(true);
    setError(null);
    try {
      onUpdated(await operation());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed");
    } finally {
      setBusy(false);
    }
  };
  const submitDialog = async (reason: string) => {
    if (dialog === "approve")
      await run(() => decideReview(review.id, "local.user", "approved"));
    else if (dialog === "dismiss-all")
      await run(() => decideReview(review.id, "local.user", "dismissed"));
    else if (dialog === "dismiss" && selected)
      await run(() =>
        dismissFinding(review.id, selected.id, "local.user", reason),
      );
    else if (dialog === "comment")
      await run(() => addComment(review.id, reason, selected?.id));
  };
  return (
    <section className="panel">
      <div className="review-summary">
        <div>
          <h3 className="summary-title">Review summary</h3>
          <div className="summary-meta">
            <StatusBadge status={review.status} />
            <span>
              <strong>{openFindings.length}</strong> open findings
            </span>
            <span>Analyzed in 42s</span>
            <span>{review.comments.length} comments</span>
          </div>
        </div>
        <div className="summary-actions">
          <button
            className="button"
            type="button"
            disabled={busy}
            onClick={() => setDialog("dismiss-all")}
          >
            <X className="icon" />
            Dismiss all
          </button>
          <button
            className="button primary"
            type="button"
            disabled={busy}
            onClick={() => setDialog("approve")}
          >
            <Check className="icon" />
            Approve review
          </button>
        </div>
      </div>
      {error && (
        <div className="inline-error" role="alert">
          <span>{error}</span>
          <button
            className="button ghost"
            type="button"
            onClick={() => setError(null)}
          >
            <X className="icon" />
          </button>
        </div>
      )}
      <div className="review-layout">
        <aside className="review-sidebar">
          <div className="subpanel-header">
            <h3>Changed files</h3>
            <span>{files.length}</span>
          </div>
          <div className="file-list">
            {files.map((file, index) => (
              <button
                className={`file-item ${file === currentFile ? "selected" : ""}`}
                type="button"
                key={file}
                onClick={() => setCurrentFile(file)}
              >
                <FileCode2 className="file-icon" />
                <span>{file.split("/").pop()}</span>
                {index < review.findings.length && (
                  <span className="file-count">
                    {review.findings[index] ? 1 : 0}
                  </span>
                )}
              </button>
            ))}
          </div>
        </aside>
        <div className="review-main">
          <div className="review-tabs">
            <button
              className={`review-tab ${tab === "changes" ? "active" : ""}`}
              type="button"
              onClick={() => setTab("changes")}
            >
              Changes
            </button>
            <button
              className={`review-tab ${tab === "summary" ? "active" : ""}`}
              type="button"
              onClick={() => setTab("summary")}
            >
              Summary
            </button>
            <button
              className={`review-tab ${tab === "checks" ? "active" : ""}`}
              type="button"
              onClick={() => setTab("checks")}
            >
              Checks <span className="muted">2</span>
            </button>
          </div>
          {tab === "changes" && (
            <>
              <div className="diff-toolbar">
                <span className="mono">{currentFile || "No changed files"}</span>
                <span>{Math.max(1, files.indexOf(currentFile) + 1)} of {files.length} files</span>
              </div>
              <div className="diff-code">
                {codeLines.map(([oldLine, newLine, code]) => (
                  <div
                    className={`code-line ${code.startsWith("+") ? "added" : ""} ${newLine === String(selected?.line) ? "marked" : ""}`}
                    key={`${oldLine}-${newLine}`}
                  >
                    <span className="line-no">{oldLine}</span>
                    <span className="line-no">{newLine}</span>
                    <code className="code-text">{code}</code>
                  </div>
                ))}
              </div>
            </>
          )}
          {tab === "summary" && (
            <div className="tab-content">
              <h3>Review summary</h3>
              <p>
                Two specialist agents analyzed this change. Findings are
                suggestions grounded in the changed lines and should be
                confirmed by a human reviewer.
              </p>
              <div className="summary-check">
                <span>Analysis coverage</span>
                <strong>100%</strong>
              </div>
              <div className="progress">
                <span style={{ width: "100%" }} />
              </div>
            </div>
          )}
          {tab === "checks" && (
            <div className="tab-content">
              <h3>Checks completed</h3>
              <div className="check-row">
                <Check className="icon" />
                Security analysis <span>Completed</span>
              </div>
              <div className="check-row">
                <Check className="icon" />
                Quality analysis <span>Completed</span>
              </div>
            </div>
          )}
        </div>
        <aside className="findings-panel">
          <div className="subpanel-header">
            <h3>Findings</h3>
            <span>{openFindings.length} open</span>
          </div>
          <div className="finding-list">
            {openFindings.length ? (
              openFindings.map((finding) => (
                <button
                  className={`finding ${finding.id === selectedId ? "selected" : ""}`}
                  type="button"
                  key={finding.id}
                  onClick={() => setSelectedId(finding.id)}
                >
                  <div className="finding-heading">
                    <Severity value={finding.severity} />
                    <strong>{finding.summary}</strong>
                  </div>
                  <p>
                    {finding.category.replaceAll("-", " ")} · {finding.agent}{" "}
                    agent
                  </p>
                  <div className="finding-meta">
                    <span className="mono">
                      {finding.file}:{finding.line}
                    </span>
                    <span>
                      {Math.round(finding.confidence * 100)}% confidence
                    </span>
                  </div>
                </button>
              ))
            ) : (
              <div className="empty">
                <div>
                  <ShieldCheck className="icon" />
                  <strong>Looks clear</strong>
                  <span>No actionable findings.</span>
                </div>
              </div>
            )}
          </div>
          {selected && (
            <div className="finding-detail">
              <div className="detail-heading">
                <h4>{selected.summary}</h4>
                <button
                  className="button ghost"
                  type="button"
                  aria-label="Dismiss finding"
                  disabled={busy}
                  onClick={() => setDialog("dismiss")}
                >
                  <X className="icon" />
                </button>
              </div>
              <div className="detail-section">
                <div className="detail-label">Why this matters</div>
                <p>
                  The refreshed token path can return a session before the role
                  check runs. A caller with an expired role may retain access
                  longer than intended.
                </p>
              </div>
              <div className="detail-section">
                <div className="detail-label">Suggested next step</div>
                <p>
                  Add the role assertion before issuing the refreshed token and
                  cover the denial path with a regression test.
                </p>
              </div>
              <div className="detail-section">
                <div className="detail-label">Review decision</div>
                <div className="actions">
                  <button
                    className="button primary"
                    type="button"
                    disabled={busy}
                    onClick={() =>
                      void run(() => resolveFinding(review.id, selected.id))
                    }
                  >
                    <Check className="icon" />
                    Resolve
                  </button>
                  <button
                    className="button"
                    type="button"
                    disabled={busy}
                    onClick={() => setDialog("comment")}
                  >
                    <MessageSquareWarning className="icon" />
                    Comment
                  </button>
                </div>
              </div>
            </div>
          )}
        </aside>
      </div>
      {dialog === "comment" ? (
        <ActionDialog
          title="Add review comment"
          description="Leave context for the author or another reviewer."
          onClose={() => setDialog(null)}
          onSubmit={submitDialog}
        />
      ) : dialog === "dismiss" ? (
        <ActionDialog
          title="Dismiss finding"
          description="Important findings need a reason so the decision remains auditable."
          requireReason
          onClose={() => setDialog(null)}
          onSubmit={submitDialog}
        />
      ) : dialog === "dismiss-all" ? (
        <ActionDialog
          title="Dismiss all findings"
          description="This will mark the review dismissed and keep the reason in its history."
          requireReason
          onClose={() => setDialog(null)}
          onSubmit={submitDialog}
        />
      ) : dialog === "approve" ? (
        <ActionDialog
          title="Approve review"
          description="Confirm that this review is ready to move forward."
          requireReason
          onClose={() => setDialog(null)}
          onSubmit={submitDialog}
        />
      ) : null}
    </section>
  );
}
