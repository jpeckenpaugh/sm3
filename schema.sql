-- Matsya: SQLite Schema
-- From Saraswati's handoff

CREATE TABLE IF NOT EXISTS profiles (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    version     TEXT    NOT NULL DEFAULT '0.1.0',
    header      TEXT    DEFAULT '{}',       -- JSON
    permissions TEXT    DEFAULT '{}',       -- JSON
    preamble    TEXT    DEFAULT '',
    body        TEXT    DEFAULT '',
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
