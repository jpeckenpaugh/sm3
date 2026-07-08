import json
import sqlite3
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

DB_PATH = "/tmp/ai-social/social.db"

app = FastAPI(title="State Machine Operator Dashboard")

import jinja2
_jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=True,
    cache_size=0,
)
_jinja_env.filters["json_pretty"] = lambda v: json.dumps(
    json.loads(v) if isinstance(v, str) else v, indent=2
)


def render(name: str, **context) -> str:
    tmpl = _jinja_env.get_template(name)
    return tmpl.render(**context)


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_all(query, params=()):
    conn = db()
    try:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def fetch_one(query, params=()):
    rows = fetch_all(query, params)
    return rows[0] if rows else None


def duration(start, end):
    if not start or not end:
        return ""
    import datetime
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    try:
        s = datetime.datetime.strptime(start, fmt)
        e = datetime.datetime.strptime(end, fmt)
        delta = e - s
        total = int(delta.total_seconds())
        if total < 60:
            return f"{total}s"
        return f"{total // 60}m {total % 60}s"
    except (ValueError, TypeError):
        return ""


@app.get("/", response_class=HTMLResponse)
async def home():
    active_sprint = fetch_one("SELECT * FROM sprints WHERE status = 'active' LIMIT 1")
    recent_runs = fetch_all(
        "SELECT pr.*, s.number AS sprint_number FROM phase_runs pr "
        "JOIN sprints s ON pr.sprint_id = s.id ORDER BY pr.id DESC LIMIT 10"
    )
    dispatch_stats = fetch_all(
        "SELECT status, COUNT(*) AS count FROM dispatch_log GROUP BY status"
    )
    phase_stats = fetch_all(
        "SELECT status, COUNT(*) AS count FROM phase_runs GROUP BY status"
    )
    pipeline_states_count = fetch_one("SELECT COUNT(*) AS count FROM pipeline_states")
    profiles_count = fetch_one("SELECT COUNT(*) AS count FROM profiles")
    components_count = fetch_one("SELECT COUNT(*) AS count FROM components")
    return HTMLResponse(render("home.html",
        path="/", active_sprint=active_sprint,
        recent_runs=recent_runs,
        dispatch_stats=dispatch_stats,
        phase_stats=phase_stats,
        pipeline_states_count=pipeline_states_count["count"] if pipeline_states_count else 0,
        profiles_count=profiles_count["count"] if profiles_count else 0,
        components_count=components_count["count"] if components_count else 0,
        duration=duration,
    ))


@app.get("/sprints", response_class=HTMLResponse)
async def sprints_list():
    sprints = fetch_all("SELECT * FROM sprints ORDER BY number DESC")
    return HTMLResponse(render("sprints.html",
        path="/sprints", sprints=sprints,
    ))


@app.get("/sprints/{sprint_id}", response_class=HTMLResponse)
async def sprint_detail(sprint_id: int):
    sprint = fetch_one("SELECT * FROM sprints WHERE id = ?", (sprint_id,))
    if not sprint:
        return HTMLResponse("Sprint not found", status_code=404)
    phase_runs = fetch_all(
        "SELECT * FROM phase_runs WHERE sprint_id = ? ORDER BY iteration, attempt",
        (sprint_id,),
    )
    dispatch_logs = fetch_all(
        "SELECT * FROM dispatch_log WHERE sprint_id = ? ORDER BY id DESC",
        (sprint_id,),
    )
    phase_events = fetch_all(
        "SELECT * FROM phase_events WHERE sprint_id = ? ORDER BY id DESC LIMIT 50",
        (sprint_id,),
    )
    return HTMLResponse(render("sprint_detail.html",
        path="/sprints/" + str(sprint_id), sprint=sprint,
        phase_runs=phase_runs,
        dispatch_logs=dispatch_logs,
        phase_events=phase_events,
        duration=duration,
    ))


@app.get("/phases", response_class=HTMLResponse)
async def phases_log():
    runs = fetch_all(
        "SELECT pr.*, s.number AS sprint_number FROM phase_runs pr "
        "JOIN sprints s ON pr.sprint_id = s.id ORDER BY pr.id DESC"
    )
    return HTMLResponse(render("phases.html",
        path="/phases", runs=runs,
        duration=duration,
    ))


@app.get("/dispatch", response_class=HTMLResponse)
async def dispatch_log():
    logs = fetch_all("SELECT * FROM dispatch_log ORDER BY id DESC")
    return HTMLResponse(render("dispatch.html",
        path="/dispatch", logs=logs,
    ))


@app.get("/profiles", response_class=HTMLResponse)
async def profiles_list():
    profiles = fetch_all(
        "SELECT p.*, COUNT(pc.id) AS component_count "
        "FROM profiles p "
        "LEFT JOIN profile_components pc ON pc.profile_id = p.id "
        "GROUP BY p.id "
        "ORDER BY p.name"
    )
    return HTMLResponse(render("profiles.html",
        path="/profiles", profiles=profiles,
    ))


@app.get("/profiles/{profile_id}", response_class=HTMLResponse)
async def profile_detail(profile_id: int):
    profile = fetch_one("SELECT * FROM profiles WHERE id = ?", (profile_id,))
    if not profile:
        return HTMLResponse("Profile not found", status_code=404)
    components = fetch_all(
        "SELECT c.*, pc.order_idx, pc.params "
        "FROM profile_components pc "
        "JOIN components c ON c.id = pc.component_id "
        "WHERE pc.profile_id = ? "
        "ORDER BY pc.order_idx",
        (profile_id,),
    )
    pipeline_state = fetch_one(
        "SELECT * FROM pipeline_states WHERE agent_name = ?",
        (profile["name"],),
    )
    return HTMLResponse(render("profile_detail.html",
        path="/profiles/" + str(profile_id), profile=profile,
        components=components,
        pipeline_state=pipeline_state,
    ))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001)
