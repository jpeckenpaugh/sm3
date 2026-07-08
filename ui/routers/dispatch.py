from fastapi import APIRouter, Request, Query
from db import query
from templates import templates

router = APIRouter()


@router.get("/dispatch")
async def dispatch_list(
    request: Request,
    sprint_id: int | None = Query(None),
    agent_name: str | None = Query(None),
    limit: int = Query(50),
):
    rows = query("""
        SELECT * FROM dispatch_log
        WHERE (?1 IS NULL OR sprint_id = ?1)
          AND (?2 IS NULL OR agent_name = ?2)
        ORDER BY id DESC
        LIMIT ?3
    """, (sprint_id, agent_name, limit))
    sprints = query("SELECT id, number FROM sprints ORDER BY number DESC")
    agents = query("SELECT DISTINCT agent_name FROM dispatch_log ORDER BY agent_name")
    return templates.TemplateResponse(request, "dispatch.html", {
        "dispatches": rows,
        "sprints": sprints,
        "agents": [r["agent_name"] for r in agents],
        "selected_sprint": sprint_id,
        "selected_agent": agent_name,
        "selected_limit": limit,
    })
