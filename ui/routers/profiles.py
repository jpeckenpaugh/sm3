import json
from fastapi import APIRouter, Request
from db import query
from templates import templates

router = APIRouter()


@router.get("/profiles")
async def profile_list(request: Request):
    rows = query("""
        SELECT p.*,
          (SELECT COUNT(*) FROM profile_components WHERE profile_id = p.id) AS component_count
        FROM profiles p
        ORDER BY p.name
    """)
    profiles = []
    for r in rows:
        d = dict(r)
        try:
            d["header_parsed"] = json.loads(d["header"])
        except (json.JSONDecodeError, TypeError):
            d["header_parsed"] = {}
        try:
            d["perms_parsed"] = json.loads(d["permissions"])
        except (json.JSONDecodeError, TypeError):
            d["perms_parsed"] = {}
        profiles.append(d)
    return templates.TemplateResponse(request, "profiles.html", {
        "profiles": profiles,
    })
