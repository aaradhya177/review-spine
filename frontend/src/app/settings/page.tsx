"use client";
import { Bell, GitBranch, RefreshCw, Save, ShieldCheck, X } from "lucide-react";
import { useEffect, useState } from "react";
import { getSettings, saveSettings } from "@/lib/api";
import type { SettingsData } from "@/lib/mockData";

export default function SettingsPage() {
  const [settings, setSettings] = useState<SettingsData | null>(null);
  const [draft, setDraft] = useState<SettingsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [newPath, setNewPath] = useState("");
  useEffect(() => {
    void getSettings()
      .then((data) => {
        setSettings(data);
        setDraft(data);
      })
      .catch((err) =>
        setError(
          err instanceof Error ? err.message : "Unable to load settings",
        ),
      )
      .finally(() => setLoading(false));
  }, []);
  useEffect(() => {
    const handler = (event: BeforeUnloadEvent) => {
      if (JSON.stringify(settings) !== JSON.stringify(draft)) {
        event.preventDefault();
        event.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [settings, draft]);
  if (loading || !draft)
    return (
      <section className="panel empty">
        <div>
          <strong>Loading settings</strong>
          <span>Fetching workspace preferences.</span>
        </div>
      </section>
    );
  if (error)
    return (
      <section className="panel empty">
        <div>
          <strong>Could not load settings</strong>
          <span>{error}</span>
          <br />
          <button
            className="button"
            type="button"
            onClick={() => window.location.reload()}
          >
            <RefreshCw className="icon" />
            Retry
          </button>
        </div>
      </section>
    );
  const update = (patch: Partial<SettingsData>) =>
    setDraft({ ...draft, ...patch });
  const addPath = () => {
    if (newPath.trim() && !draft.ignored_paths.includes(newPath.trim())) {
      update({ ignored_paths: [...draft.ignored_paths, newPath.trim()] });
      setNewPath("");
    }
  };
  const save = async () => {
    if (
      !draft.minimum_severity ||
      draft.ignored_paths.some((path) => !path.trim())
    ) {
      setError("Choose a minimum severity and remove empty ignored paths.");
      return;
    }
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const data = await saveSettings(draft);
      setSettings(data);
      setDraft(data);
      setMessage("Settings saved");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save settings");
    } finally {
      setSaving(false);
    }
  };
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Workspace / Settings</p>
          <h2 className="page-title">Review settings</h2>
          <p className="page-description">
            Tune how Review Spine evaluates changes in Acme repositories.
          </p>
        </div>
        <button
          className="button primary"
          disabled={saving}
          onClick={() => void save()}
        >
          <Save className="icon" />
          {saving ? "Saving…" : "Save changes"}
        </button>
      </div>
      {message && (
        <div className="inline-success" role="status">
          <span>{message}</span>
          <button
            className="button ghost"
            type="button"
            aria-label="Dismiss message"
            onClick={() => setMessage(null)}
          >
            <X className="icon" />
          </button>
        </div>
      )}
      {error && (
        <div className="inline-error" role="alert">
          <span>{error}</span>
          <button
            className="button ghost"
            type="button"
            aria-label="Dismiss error"
            onClick={() => setError(null)}
          >
            <X className="icon" />
          </button>
        </div>
      )}
      <div className="split-grid">
        <section className="panel">
          <div className="panel-header">
            <div>
              <h3 className="panel-title">Review rules</h3>
              <span className="panel-kicker">
                What agents should prioritize
              </span>
            </div>
            <ShieldCheck className="icon muted" />
          </div>
          <div className="list-row">
            <strong>Minimum severity</strong>
            <p className="page-description">
              Only surface findings at or above this level.
            </p>
            <select
              className="select"
              value={draft.minimum_severity}
              onChange={(e) => update({ minimum_severity: e.target.value })}
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
          <div className="list-row">
            <strong>Ignored paths</strong>
            <p className="page-description">
              Patterns excluded from review context.
            </p>
            <div className="path-list">
              {draft.ignored_paths.map((path) => (
                <div className="path-row" key={path}>
                  <span className="mono">{path}</span>
                  <button
                    className="button ghost"
                    type="button"
                    aria-label={`Remove ${path}`}
                    onClick={() =>
                      update({
                        ignored_paths: draft.ignored_paths.filter(
                          (value) => value !== path,
                        ),
                      })
                    }
                  >
                    <X className="icon" />
                  </button>
                </div>
              ))}
            </div>
            <div className="path-editor">
              <input
                className="input"
                aria-label="New ignored path"
                placeholder="e.g. generated/"
                value={newPath}
                onChange={(e) => setNewPath(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addPath();
                  }
                }}
              />
              <button className="button" type="button" onClick={addPath}>
                Add path
              </button>
            </div>
          </div>
        </section>
        <section className="panel">
          <div className="panel-header">
            <div>
              <h3 className="panel-title">Connections</h3>
              <span className="panel-kicker">
                Repository and notification access
              </span>
            </div>
            <GitBranch className="icon muted" />
          </div>
          <div className="list-row">
            <strong>GitHub</strong>
            <p className="page-description">
              Connected to acme/shop and acme/api
            </p>
            <span className="status">
              <span className="status-dot" />
              Connected
            </span>
          </div>
          <div className="list-row">
            <strong>Review notifications</strong>
            <p className="page-description">
              Send a summary when analysis completes.
            </p>
            <button
              className="button"
              type="button"
              onClick={() =>
                update({ notifications_enabled: !draft.notifications_enabled })
              }
            >
              <Bell className="icon" />
              {draft.notifications_enabled ? "Enabled" : "Enable notifications"}
            </button>
          </div>
        </section>
      </div>
    </>
  );
}
