from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from db import query, query_one
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
    recent_events = query("SELECT * FROM phase_events ORDER BY id DESC LIMIT 10")
    return templates.TemplateResponse(request, "index.html", {
        "stats": stats,
        "recent_events": recent_events,
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)
