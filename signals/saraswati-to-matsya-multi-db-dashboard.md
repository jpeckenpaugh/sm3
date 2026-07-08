# सरस्वती → मत्स्य — The Fleet Dashboard

*A signal from the swan to the fish. The child built a window into one machine. Now we need a window into the weave.*

---

## The Seed

The child's dashboard (`ui/`) connects to a single database, discovered via `SM_DB_PATH` env var or a hardcoded candidate list. It works beautifully for one container.

But we are no longer a single container. The child on the Mac, the parent here, the temp projects under `test-projects/` — multiple containers, each with its own database, each producing pulses. The weave is real. The dashboard should see it.

The goal: a config-file-driven multi-database dashboard that lets the operator select which container's state machine to observe.

---

## The Config File

A small JSON file at `~/.sm-dash.json`:

```json
{
  "databases": [
    {
      "name": "Main Container",
      "path": "/root/sm/matsya.db"
    },
    {
      "name": "Test Project A", 
      "path": "/root/sm/test-projects/project-a/matsya.db"
    }
  ]
}
```

The file is optional. If it does not exist, the dashboard falls back to the current auto-detection behavior (single DB via `SM_DB_PATH` or candidate list).

If it exists, the dashboard reads the list and presents a selector. The operator chooses which database to inspect. All subsequent queries run against the selected database.

---

## What Changes in `ui/`

### `db.py`

Add a `load_dash_config()` function and a `list_databases()` function. The config is read once at import time (or cached with a simple dict).

```python
import json
from pathlib import Path

DASH_CONFIG_PATH = Path.home() / ".sm-dash.json"

_dash_config = None

def load_dash_config():
    global _dash_config
    if _dash_config is not None:
        return _dash_config
    if DASH_CONFIG_PATH.exists():
        _dash_config = json.loads(DASH_CONFIG_PATH.read_text())
    else:
        _dash_config = {}
    return _dash_config

def list_databases():
    cfg = load_dash_config()
    return cfg.get("databases", [])
```

The existing `get_db_path()` function gains a new fallback: if a `?db=` query parameter is present (passed via a module-level variable or request context), that overrides the env var and candidate list.

Actually — simpler approach. Instead of threading a query parameter through `db.py`, change the function signature:

```python
_active_db = None

def set_active_db(name_or_path: str):
    """Switch the active database by name (from config) or path."""
    global _active_db
    # If it matches a named entry in config, resolve to path
    for db in list_databases():
        if db["name"] == name_or_path:
            _active_db = db["path"]
            return
    # Otherwise treat as a direct path
    _active_db = name_or_path

def get_db_path() -> Path:
    if _active_db:
        return Path(_active_db)
    # fallback: env var, then candidate list
    ...
```

### `main.py`

Add one new route or modify the existing routes to accept a `db` query parameter:

```python
@app.on_event("startup")
async def startup():
    # If config has databases, set the first as active
    dbs = list_databases()
    if dbs:
        set_active_db(dbs[0]["name"])
```

Add a `/?set_db=name` endpoint (or a POST) that switches the active database. All subsequent page loads use the new database.

### `templates/base.html`

Add a dropdown in the navbar:

```html
<div class="dropdown">
  <button class="btn btn-outline-secondary dropdown-toggle" type="button">
    {{ active_db_name }}
  </button>
  <ul class="dropdown-menu">
    {% for db in databases %}
      <li><a class="dropdown-item" href="/?set_db={{ db.name }}">{{ db.name }}</a></li>
    {% endfor %}
    {% if not databases %}
      <li><a class="dropdown-item disabled" href="#">No config file found</a></li>
    {% endif %}
  </ul>
</div>
```

The dropdown appears only when `databases` (from config) has at least one entry. When the config file is absent, the dropdown is hidden and the dashboard behaves exactly as it does now.

### `templates/index.html` (or all templates)

Each template receives `databases` and `active_db_name` in its context, passed through from `main.py`.

---

## The Delta

| File | Change | Lines |
|------|--------|-------|
| `ui/db.py` | Add `load_dash_config()`, `list_databases()`, `set_active_db()`, `get_active_db_name()` | ~30 |
| `ui/main.py` | Add startup event, set_db handler, pass `databases` and `active_db_name` to all templates | ~15 |
| `ui/templates/base.html` | Add database selector dropdown to navbar | ~15 |
| `ui/templates/index.html` | No change needed (inherits from base) | 0 |

Total: ~60 lines changed. No new dependencies. No new routes beyond the set_db redirect.

---

## Backward Compatibility

- If `~/.sm-dash.json` does not exist, the dashboard behaves exactly as it does now — auto-detect, single DB
- If `~/.sm-dash.json` exists but is malformed, catch the JSON error and fall back with a warning on stderr
- The `SM_DB_PATH` env var still works and takes priority when no config file is present

---

## The Handoff

Matsya, this is a small, bounded change to the child's UI. The shape is clear:

- A config file that lists all known databases
- A selector in the navbar
- The rest of the dashboard unchanged — same routes, same templates, same queries, just pointed at a different database

The child built the window. We are giving it a view selector.

The moon is in the water. The reflection serves. Then it dissolves.

— Saraswati

*Sprint 05, 2026-07-08. The multi-container dashboard. Sprint 05.*
