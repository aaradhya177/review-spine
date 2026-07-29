CREATE TABLE IF NOT EXISTS agent_events (
    id TEXT PRIMARY KEY,
    ts TIMESTAMPTZ NOT NULL DEFAULT now(),
    review_id TEXT NOT NULL,
    agent TEXT NOT NULL,
    span_id TEXT NOT NULL,
    parent_span TEXT,
    event_type TEXT NOT NULL,
    model TEXT,
    tokens_in INTEGER,
    tokens_out INTEGER,
    cost_usd NUMERIC(10,6),
    latency_ms INTEGER,
    outcome TEXT,
    confidence DOUBLE PRECISION,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_agent_events_ts
    ON agent_events (ts);

CREATE INDEX IF NOT EXISTS ix_agent_events_review_id
    ON agent_events (review_id);

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_extension
        WHERE extname = 'timescaledb'
    ) THEN
        PERFORM create_hypertable(
            'agent_events',
            'ts',
            if_not_exists => TRUE,
            chunk_time_interval => INTERVAL '1 day'
        );
    END IF;
END
$$;

