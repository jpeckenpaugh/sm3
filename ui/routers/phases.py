from fastapi import APIRouter, Request, Query
from db import query
from templates import templates

router = APIRouter()


@router.get("/phases")
async def phase_list(
    request: Request,
    sprint_id: int | None = Query(None),
    phase: str | None = Query(None),
    limit: int = Query(50),
):
    rows = query("""
        SELECT pr.*,
          (SELECT COUNT(*) FROM phase_events
           WHERE sprint_id = pr.sprint_id AND phase = pr.phase
             AND iteration = pr.iteration AND attempt = pr.attempt) AS event_count
        FROM phase_runs pr
        WHERE (?1 IS NULL OR sprint_id = ?1)
          AND (?2 IS NULL OR phase = ?2)
        ORDER BY pr.id DESC
        LIMIT ?3
    """, (sprint_id, phase, limit))
    sprints = query("SELECT id, number FROM sprints ORDER BY number DESC")
    phases_list = query("SELECT DISTINCT phase FROM phase_runs ORDER BY phase")
    return templates.TemplateResponse(request, "phases.html", {
        "phases": rows,
        "sprints": sprints,
        "phases_list": [r["phase"] for r in phases_list],
        "selected_sprint": sprint_id,
        "selected_phase": phase,
        "selected_limit": limit,
    })
