CREATE TABLE IF NOT EXISTS tickets (
    id            SERIAL PRIMARY KEY,
    customer      VARCHAR(120) NOT NULL,
    plan          VARCHAR(20)  NOT NULL DEFAULT 'free',   -- free | pro | enterprise
    subject       VARCHAR(255) NOT NULL,
    body          TEXT         NOT NULL,
    category      VARCHAR(40),
    sentiment     REAL,                                   -- -1 (angry) .. +1 (happy)
    priority      VARCHAR(10),                            -- P1 (urgent) .. P4 (low)
    score         REAL,                                   -- 0..100
    reasons       TEXT,
    status        VARCHAR(20)  NOT NULL DEFAULT 'open',
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_tickets_queue ON tickets (status, score DESC);
