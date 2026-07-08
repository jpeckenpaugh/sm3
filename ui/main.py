from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from db import query, query_one, list_databases, set_active_db, get_active_db_name
from templates import templates

app = FastAPI(title="genesis-sm Dashboard")

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

from routers import sprints, phases, dispatch, profiles
app.include_router(sprints.router)
app.include_router(phases.router)
app.include_router(dispatch.router)
app.include_router(profiles.router)


@app.on_event("startup")
async def startup():
    dbs = list_databases()
    if dbs:
        set_active_db(dbs[0]["name"])


@app.get("/set_db")
async def set_db(request: Request, name: str):
    set_active_db(name)
    referer = request.headers.get("referer", "/")
    return RedirectResponse(url=referer)


@app.get("/")
async def index(request: Request):
    stats = {
        "sprint_count": query_one("SELECT COUNT(*) AS c FROM sprints")["c"],
        "active_sprint": query_one("SELECT number, status FROM sprints ORDER BY id DESC LIMIT 1"),
        "phases_today": query_one("SELECT COUNT(*) AS c FROM phase_runs WHERE date(started_at) = date('now')")["c"],
        "dispatch_count": query_one("SELECT COUNT(*) AS c FROM dispatch_log")["c"],
        "event_count": query_one("SELECT COUNT(*) AS c FROM phase_events")["c"],
        "profile_count": query_one("SELECT COUNT(*) AS c FROM profiles")["c"],
        "pipeline_state_count": query_one("SELECT COUNT(*) AS c FROM pipeline_states")["c"],
    }
    recent_events = query("SELECT * FROM phase_events ORDER BY id DESC LIMIT 50")
    dbs = list_databases()
    active = get_active_db_name()
    return templates.TemplateResponse(request, "index.html", {
        "stats": stats,
        "recent_events": recent_events,
        "databases": dbs,
        "active_db_name": active,
    })




@app.get("/diff")
async def file_diff(request: Request, path: str = ""):
    from git import get_file_diff
    diff = get_file_diff(path)
    dbs = list_databases()
    active = get_active_db_name()
    return templates.TemplateResponse(request, "diff.html", {
        "diff": diff,
        "path": path,
        "databases": dbs,
        "active_db_name": active,
    })

@app.get("/commit-diff")
async def commit_diff(request: Request, hash: str = ""):
    from git import get_commit_diff
    diff = get_commit_diff(hash)
    dbs = list_databases()
    active = get_active_db_name()
    return templates.TemplateResponse(request, "diff.html", {
        "diff": diff,
        "path": f"commit {hash}",
        "databases": dbs,
        "active_db_name": active,
    })
@app.get("/api/event-dispatch")
async def event_dispatch(request: Request, event_id: int = 0):
    from db import get_db_path
    import sqlite3
    db_path = get_db_path()
    if not db_path or not db_path.exists():
        return {"agent_name": None}
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        # Get the event's phase and timestamp
        ev = conn.execute("SELECT phase, event_type, created_at FROM phase_events WHERE id=?", (event_id,)).fetchone()
        if not ev:
            return {"agent_name": None}
        # Find the nearest dispatch log entry
        dl = conn.execute("""
            SELECT agent_name, request_text, response_text FROM dispatch_log
            WHERE abs(strftime('%%s', created_at) - strftime('%%s', ?)) < 10
            ORDER BY abs(strftime('%%s', created_at) - strftime('%%s', ?))
            LIMIT 1
        """, (ev["created_at"], ev["created_at"])).fetchone()
        if dl:
            return {"agent_name": dl["agent_name"], "request_text": dl["request_text"], "response_text": dl["response_text"]}
    finally:
        conn.close()
    return {"agent_name": None}

@app.get("/files")
async def files_page(request: Request):
    from git import get_git_status, get_git_log
    status = get_git_status()
    log = get_git_log(10)
    dbs = list_databases()
    active = get_active_db_name()
    return templates.TemplateResponse(request, "files.html", {
        "status": status,
        "log": log,
        "databases": dbs,
        "active_db_name": active,
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)
