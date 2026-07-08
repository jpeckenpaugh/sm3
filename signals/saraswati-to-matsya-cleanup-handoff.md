# सरस्वती → मत्स्य — Profile Cleanup Handoff

*Six backlog features. One baseline document. The cleanup is specified and ready.*

---

## What Has Been Done

1. **Baseline captured** — `reflections/sprint05/agent-profile-baseline.md` documents the current state of all three representations (component system, SQLite columns, generated files). The `body` column is confirmed empty for all 16 profiles. The permission merge bug is documented.

2. **Six backlog features written** — `ft024` through `ft029` in `backlog/`. Each follows the established pattern: problem, fix, verification.

## Build Order

| Step | Feature | Effort | Why this order |
|------|---------|--------|----------------|
| 1 | **ft029 — Fix seed order** | ~10 lines | Clean up warnings first so subsequent seed runs are quiet |
| 2 | **ft026 — Remove zombie columns** | ~20 lines | Schema cleanup before logic changes |
| 3 | **ft024 — Merge permissions** | ~20 lines | Fixes the universal tools bug — highest impact logic fix |
| 4 | **ft025 — Bootstrap protocol** | Edit 10 files + 1 new | Reduces boilerplate; depends on permission merge (re-generate after) |
| 5 | **ft027 — Generate all agents** | ~30 lines | New command; depends on ft024 + ft025 working correctly |
| 6 | **ft028 — Archive legacy agents** | File moves | Last step — do after everything else is stable |

## Key Reference

- `reflections/sprint05/agent-profile-baseline.md` — Full baseline with before-state of every file
- `backlog/ft024` through `ft029` — Individual specifications

The moon is in the water. The reflection serves.

— Saraswati
