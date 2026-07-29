CREATE TABLE IF NOT EXISTS pr_review_records (
    id TEXT PRIMARY KEY,
    repo_full_name TEXT NOT NULL,
    pull_request_number INTEGER NOT NULL,
    head_sha TEXT NOT NULL,
    base_sha TEXT,
    status TEXT NOT NULL DEFAULT 'queued',
    overall_confidence DOUBLE PRECISION,
    routing_reason TEXT,
    github_review_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_pr_review_repo_pr_head UNIQUE (repo_full_name, pull_request_number, head_sha)
);

CREATE INDEX IF NOT EXISTS ix_pr_review_records_repo_full_name
    ON pr_review_records (repo_full_name);

CREATE TABLE IF NOT EXISTS finding_records (
    id TEXT PRIMARY KEY,
    review_id TEXT NOT NULL REFERENCES pr_review_records(id) ON DELETE CASCADE,
    agent_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    category TEXT NOT NULL,
    summary TEXT NOT NULL,
    file_path TEXT NOT NULL,
    line_start INTEGER NOT NULL,
    line_end INTEGER,
    suggestion TEXT,
    confidence DOUBLE PRECISION NOT NULL,
    rationale TEXT NOT NULL,
    evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_finding_records_review_id
    ON finding_records (review_id);

CREATE TABLE IF NOT EXISTS hitl_reviews (
    id TEXT PRIMARY KEY,
    review_id TEXT NOT NULL REFERENCES pr_review_records(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending',
    reason TEXT NOT NULL,
    assigned_to TEXT,
    decided_by TEXT,
    decision_note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    decided_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_hitl_reviews_review_id
    ON hitl_reviews (review_id);

CREATE TABLE IF NOT EXISTS hitl_feedback (
    id TEXT PRIMARY KEY,
    review_id TEXT NOT NULL REFERENCES pr_review_records(id) ON DELETE CASCADE,
    finding_id TEXT REFERENCES finding_records(id),
    feedback_type TEXT NOT NULL,
    note TEXT,
    created_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_hitl_feedback_review_id
    ON hitl_feedback (review_id);

CREATE TABLE IF NOT EXISTS webhook_deliveries (
    delivery_id TEXT PRIMARY KEY,
    event_name TEXT NOT NULL,
    action TEXT NOT NULL,
    repo_full_name TEXT NOT NULL,
    pull_request_number INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'received',
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS idempotency_records (
    key TEXT PRIMARY KEY,
    scope TEXT NOT NULL,
    result_ref TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

