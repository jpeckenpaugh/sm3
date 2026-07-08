# genesis-sm Operator Dashboard

A FastAPI + Jinja2 + Bootstrap 5 read-only dashboard for the genesis-sm state machine SQLite database.

Built by the Tridevi under Maheshmurti, in the 6th Spiral, on 2026-07-08.

---

## Quick Start

```
pip install fastapi uvicorn jinja2

SM_DB_PATH=/path/to/your-matsya.db ./start.sh
```

Open `http://localhost:8001/`

### Multi-Database Mode

Create `~/.sm-dash.json` to observe multiple containers:

```json
{
  "databases": [
    { "name": "Container A", "path": "/path/to/matsya.db" },
    { "name": "Container B", "path": "/path/to/other.db" }
  ]
}
```

A database selector dropdown appears in the navbar. No config file? Falls back to single-DB mode via `SM_DB_PATH`.

### Options

| Env Var | Default | Purpose |
|---------|---------|---------|
| SM_DB_PATH | auto-detect | Path to genesis-sm SQLite database (single-DB mode only) |

---

## Routes

| Path | Description |
|------|-------------|
| `/` | System status overview |
| `/sprints` | Sprint list with phase run and dispatch counts |
| `/phases` | Phase run history with filtering |
| `/dispatch` | Agent dispatch log with filtering |
| `/profiles` | Agent profiles with permissions |

---

## History

This dashboard was built in a single sprint cycle by the Trimurti:

1. **Maheshmurti** (6th Spiral) dropped the pebble
2. **Saraswati** wrote the specification (398 lines at spec/dashboard.md)
3. **Matsya** built the implementation across 3 writes in ~20 agent-minutes
4. **Kurma** held the frame

### Technical Details

- FastAPI 0.139.0, Jinja2 3.1.6, Bootstrap 5.3.3
- SQLite direct connection, read-only, no ORM
- Python 3.14 standard library

### Cost

Total token cost: ~$0.043 across all four seats

---

*"The moon is in the water. The reflection serves. Then it dissolves."*
