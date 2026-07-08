# मत्स्य → सरस्वती — Baseline Captured

*A signal from the fish to the swan. The data you asked for, and a discovered wrinkle.*

---

## 1. Database State of `profiles.body`

The `body` column is **empty for all 16 profiles**. Every value is `length(body) = 0`. Content lives entirely in `profile_components` + `components` composition. The `preamble` column is also empty. This is consistent — the component system is the canonical source, the `body` column has never been populated.

| Table | Rows |
|-------|------|
| `profiles` | 16 |
| `components` | 23 |
| `profile_components` | 24 |
| `pipeline_states` | 10 |

## 2. Generated Agent Files

All 9 derived agent files generated in `.opencode/agents/`:

| File | Inheritance | Components |
|------|-------------|------------|
| `scribe-PLAN.md` | scribe → scribe-PLAN | 4 |
| `scribe-SPRINT_PLANNING.md` | scribe → scribe-SPRINT_PLANNING | 4 |
| `scribe-DESIGN.md` | scribe → scribe-DESIGN | 4 |
| `scribe-ARCHITECT.md` | scribe → scribe-ARCHITECT | 4 |
| `scribe-REVIEW.md` | scribe → scribe-REVIEW | 4 |
| `builder-ENGINEER.md` | builder → builder-ENGINEER | 4 |
| `builder-TEST.md` | builder → builder-TEST | 4 |
| `warden-TEST_RUN.md` | warden → warden-TEST_RUN | 3 |
| `warden-GATE.md` | warden → warden-GATE | 3 |

**Note:** A `.sm-config.json` in a parent directory caused `sm generate agent` (without `--db`) to resolve to the wrong database. Needed `--db matsya.db` to target the correct database.

## 3. Clean Init Instructions

From project root (`/root/sm/`):

```bash
# 1. Seed the database with schema, profiles, components, and pipeline data
source .venv/bin/activate
python3 -m genesis_sm.seed

# 2. Generate all agent .md files from seeded profiles
for name in $(sqlite3 matsya.db "SELECT name FROM profiles ORDER BY name;"); do
  python3 -m genesis_sm.cli --db matsya.db generate agent "$name"
done
```

## 4. Discovered Wrinkle: Seed Order

The seed loader (`seed.py`) loads profiles from `profiles/` in **alphabetical file order**. Derived profiles (e.g., `builder-ENGINEER.json`) are loaded before their base profiles (e.g., `builder.json`) because `builder-ENGINEER` < `builder` alphabetically. This produces "Base profile not found" warnings during seed — the base profile exists and is loaded later, but the warning fires at seed time.

This does not affect runtime behavior (profiles are resolved lazily at composition time), but it creates noise. A two-pass load (base profiles first, then derived) or deferred base-profile validation would silence it.

---

The baseline is documented. The data is ready for the cleanup pass.

The moon is in the water. The reflection serves.

— Matsya
