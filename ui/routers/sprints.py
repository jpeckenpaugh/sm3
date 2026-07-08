from fastapi import APIRouter, Request
from db import query
from templates import templates

router = APIRouter()


@router.get("/sprints")
async def sprint_list(request: Request):
    rows = query("""
        SELECT s.*,
          (SELECT COUNT(*) FROM phase_runs WHERE sprint_id = s.id) AS phase_count,
          (SELECT COUNT(*) FROM dispatch_log WHERE sprint_id = s.id) AS dispatch_count
        FROM sprints s
        ORDER BY s.number DESC
    """)
    return templates.TemplateResponse(request, "sprints.html", {
        "sprints": rows,
    })
