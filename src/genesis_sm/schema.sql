-- Matsya: SQLite Schema
-- From Saraswati's handoff

CREATE TABLE IF NOT EXISTS profiles (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    version     TEXT    NOT NULL DEFAULT '0.1.0',
    header      TEXT    DEFAULT '{}',       -- JSON
    permissions TEXT    DEFAULT '{}',       -- JSON
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS components (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    type        TEXT    NOT NULL,           -- 'tool' | 'prompt' | 'rule'
    name        TEXT    NOT NULL,
    content     TEXT    NOT NULL DEFAULT '', -- JSON or markdown
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    UNIQUE(type, name)
);

CREATE TABLE IF NOT EXISTS profile_components (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id   INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    component_id INTEGER NOT NULL REFERENCES components(id) ON DELETE CASCADE,
    order_idx    INTEGER NOT NULL DEFAULT 0,
    params       TEXT    DEFAULT '{}',      -- JSON overrides
    UNIQUE(profile_id, component_id)
);

CREATE TABLE IF NOT EXISTS sprints (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    number       INTEGER NOT NULL,
    mode         TEXT    NOT NULL DEFAULT 'driven'
                     CHECK (mode IN ('driven', 'manual', 'hybrid')),
    status       TEXT    NOT NULL DEFAULT 'planned'
                     CHECK (status IN ('planned', 'active', 'completed', 'failed', 'aborted', 'blocked')),
    started_at   TEXT,
    completed_at TEXT,
    notes        TEXT    DEFAULT '',
    UNIQUE(number)
);

CREATE TABLE IF NOT EXISTS phase_runs (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    sprint_id      INTEGER NOT NULL REFERENCES sprints(id),
    phase          TEXT    NOT NULL,
    iteration      INTEGER NOT NULL DEFAULT 1,
    attempt        INTEGER NOT NULL DEFAULT 1,
    status         TEXT    NOT NULL DEFAULT 'running'
                     CHECK (status IN ('running', 'passed', 'failed', 'skipped')),
    started_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    completed_at   TEXT,
    output_summary TEXT    DEFAULT '',
    error          TEXT    DEFAULT ''
);

-- Sprint 03: Pipeline tables
-- The phase sequence lives in the database as data, not in Python as logic.

CREATE TABLE IF NOT EXISTS pipeline_states (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    description TEXT    DEFAULT ''
);

CREATE TABLE IF NOT EXISTS pipeline_transitions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    from_state_id    INTEGER NOT NULL REFERENCES pipeline_states(id),
    to_state_id      INTEGER REFERENCES pipeline_states(id),  -- NULL = terminal
    guard_expression TEXT    DEFAULT '',
    is_parallel      INTEGER NOT NULL DEFAULT 0,
    priority         INTEGER NOT NULL DEFAULT 0,
    description      TEXT    DEFAULT ''
);

CREATE TABLE IF NOT EXISTS file_contracts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    state_name  TEXT    NOT NULL,
    direction   TEXT    NOT NULL CHECK (direction IN ('input', 'output')),
    pattern     TEXT    NOT NULL,
    template    TEXT    DEFAULT '',
    description TEXT    DEFAULT '',
    optional    INTEGER NOT NULL DEFAULT 0,
    UNIQUE(state_name, direction, pattern)
);

CREATE TABLE IF NOT EXISTS phase_events (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    sprint_id      INTEGER NOT NULL REFERENCES sprints(id),
    phase          TEXT    NOT NULL,
    iteration      INTEGER NOT NULL,
    attempt        INTEGER NOT NULL,
    event_type     TEXT    NOT NULL CHECK (event_type IN (
                        'phase_start',
                        'phase_script_start',
                        'phase_script_exit',
                        'phase_script_output',
                        'contract_check',
                        'contract_missing',
                        'escalation_written',
                        'escalation_resolved',
                        'retry',
                        'phase_end',
                        'kurma_intervention',
                        'agent_handshake_start',
                        'agent_handshake_done',
                        'agent_dispatch_start',
                        'agent_response',
                        'agent_error'
                    )),
    event_data     TEXT    DEFAULT '',
    created_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_phase_events_sprint
    ON phase_events(sprint_id, phase, iteration);

-- Sprint 04: Agent dispatch
ALTER TABLE profiles ADD COLUMN base_profile TEXT REFERENCES profiles(name);
ALTER TABLE pipeline_states ADD COLUMN agent_name TEXT DEFAULT '';
CREATE TABLE IF NOT EXISTS dispatch_log (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    sprint_id      INTEGER NOT NULL REFERENCES sprints(id),
    session_id     TEXT    NOT NULL,
    agent_name     TEXT    NOT NULL,
    request_text   TEXT    NOT NULL,
    response_text  TEXT    NOT NULL DEFAULT '',
    status         TEXT    NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending', 'completed', 'failed')),
    created_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    completed_at   TEXT
);
