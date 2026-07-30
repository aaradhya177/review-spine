"use client";
import { Check, MessageSquareWarning, X } from "lucide-react";
import { useState } from "react";
import { decideReview } from "@/lib/api";
import type { ReviewRow } from "@/lib/mockData";

export function HitlActions({
  review,
  onComplete,
}: {
  review: ReviewRow;
  onComplete: (review: ReviewRow) => void;
}) {
  const [dialog, setDialog] = useState<
    "approve" | "reject" | "escalate" | null
  >(null);
  const [reason, setReason] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const submit = async () => {
    if (!reason.trim()) return;
    setSaving(true);
    setError(null);
    try {
      const decision: "approved" | "rejected" | "escalated" =
        dialog === "approve"
          ? "approved"
          : dialog === "reject"
            ? "rejected"
            : "escalated";
      onComplete(await decideReview(review.id, "local.user", decision, reason));
      setDialog(null);
      setReason("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed");
    } finally {
      setSaving(false);
    }
  };
  return (
    <>
      <div className="actions">
        <button
          className="button primary"
          type="button"
          disabled={saving}
          onClick={() => setDialog("approve")}
        >
          <Check className="icon" />
          Approve
        </button>
        <button
          className="button danger"
          type="button"
          disabled={saving}
          onClick={() => setDialog("reject")}
        >
          <X className="icon" />
          Reject
        </button>
        <button
          className="button"
          type="button"
          disabled={saving}
          onClick={() => setDialog("escalate")}
        >
          <MessageSquareWarning className="icon" />
          Escalate
        </button>
      </div>
      {error && (
        <div className="inline-error" role="alert">
          {error}
        </div>
      )}
      {dialog && (
        <dialog className="dialog" open>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              void submit();
            }}
          >
            <div className="dialog-header">
              <div>
                <h3>
                  {dialog === "approve"
                    ? "Approve review"
                    : dialog === "reject"
                      ? "Reject review"
                      : "Escalate review"}
                </h3>
                <p>This decision will be saved to the review history.</p>
              </div>
              <button
                className="button ghost"
                type="button"
                aria-label="Close dialog"
                onClick={() => setDialog(null)}
              >
                <X className="icon" />
              </button>
            </div>
            <label className="field-label">
              Reason
              <textarea
                className="textarea"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Explain your decision"
                required
                autoFocus
              />
            </label>
            <div className="dialog-actions">
              <button
                className="button"
                type="button"
                onClick={() => setDialog(null)}
              >
                Cancel
              </button>
              <button
                className="button primary"
                disabled={saving || !reason.trim()}
                type="submit"
              >
                {saving ? "Saving…" : "Confirm"}
              </button>
            </div>
          </form>
        </dialog>
      )}
    </>
  );
}
