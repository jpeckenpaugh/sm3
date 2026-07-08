import os
import sqlite3
from functools import lru_cache
from pathlib import Path

def get_db_path() -> Path:
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
