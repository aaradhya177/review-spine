CREATE MATERIALIZED VIEW IF NOT EXISTS agent_health_1m AS
SELECT
    date_trunc('minute', ts) AS bucket,
    agent,
    count(*) FILTER (WHERE event_type = 'llm.call') AS llm_calls,
    sum(cost_usd) AS cost_usd,
    sum(tokens_in) AS tokens_in,
    sum(tokens_out) AS tokens_out,
    percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms) AS p95_ms
FROM agent_events
GROUP BY bucket, agent;

CREATE MATERIALIZED VIEW IF NOT EXISTS pr_cost_hourly AS
SELECT
    date_trunc('hour', ts) AS bucket,
    review_id,
    sum(cost_usd) AS total_cost_usd,
    count(DISTINCT agent) AS agents_used
FROM agent_events
WHERE event_type = 'llm.call'
GROUP BY bucket, review_id;

