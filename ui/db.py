import json
import os
import sqlite3
from functools import lru_cache
from pathlib import Path

# ─── Multi-DB config (~/.sm-dash.json) ───────────────────────────────────────

DASH_CONFIG_PATH = Path.home() / ".sm-dash.json"

_dash_config: dict | None = None
_active_db_path: str | None = None


def load_dash_config() -> dict:
    global _dash_config
    if _dash_config is not None:
        return _dash_config
    if DASH_CONFIG_PATH.exists():
        try:
            _dash_config = json.loads(DASH_CONFIG_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            _dash_config = {}
    else:
        _dash_config = {}
    return _dash_config


def list_databases() -> list[dict]:
    cfg = load_dash_config()
    return cfg.get("databases", [])


def set_active_db(name_or_path: str) -> str:
    """Switch active database by config name or direct path. Returns the resolved path."""
    global _active_db_path
    for db in list_databases():
        if db["name"] == name_or_path:
            _active_db_path = db["path"]
            return _active_db_path
    # Treat as direct path
    _active_db_path = name_or_path
    return _active_db_path


def get_active_db_name() -> str:
    """Return the display name of the currently active database."""
    if _active_db_path is None:
        return "default"
    for db in list_databases():
        if db["path"] == _active_db_path:
            return db["name"]
    return _active_db_path


def get_db_path() -> Path:
    if _active_db_path:
        return Path(_active_db_path)
    env = os.environ.get("SM_DB_PATH")
    if env:
        return Path(env)
    # Default: look for social.db in the project
    candidates = [
        Path("/tmp/ai-social/social.db"),
        Path("social.db"),
        Path("matsya.db"),
    ]
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]


# ─── Queries ─────────────────────────────────────────────────────────────────

def query(sql: str, params: tuple = ()) -> list[dict]:
    conn = sqlite3.connect(str(get_db_path()))
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(sql, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def query_one(sql: str, params: tuple = ()) -> dict | None:
    rows = query(sql, params)
    return rows[0] if rows else None
