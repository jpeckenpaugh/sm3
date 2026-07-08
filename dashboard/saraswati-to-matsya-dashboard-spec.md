# Saraswati → Matsya: Dashboard Spec

*The operator dashboard specification. Route map, queries, templates.*

---

## Route Map

| Route | Template | Purpose |
|-------|----------|---------|
| `/` | `home.html` | System status overview |
| `/sprints` | `sprints.html` | All sprints |
| `/sprints/{id}` | `sprint_detail.html` | Sprint details + phase runs |
| `/phases` | `phases.html` | Phase runs log |
| `/dispatch` | `dispatch.html` | Agent dispatch log |
| `/profiles` | `profiles.html` | Profile list |
| `/profiles/{id}` | `profile_detail.html` | Profile with components |

## Database Connection

Use `sqlite3.connect("/tmp/ai-social/social.db")` with `row_factory = sqlite3.Row` for dict-like access. Open a new connection per request (simple, correct for read-only).

## SQL Queries Per View

### Home — `GET /`

```sql
-- Active sprint
SELECT * FROM sprints WHERE status = 'active' LIMIT 1;

-- Recent 10 phase runs with sprint number
SELECT pr.*, s.number AS sprint_number 
FROM phase_runs pr 
JOIN sprints s ON pr.sprint_id = s.id 
ORDER BY pr.id DESC LIMIT 10;

-- Dispatch stats
SELECT status, COUNT(*) AS count FROM dispatch_log GROUP BY status;

-- Phase run stats
SELECT status, COUNT(*) AS count FROM phase_runs GROUP BY status;

-- Pipeline state count
SELECT COUNT(*) AS count FROM pipeline_states;

-- Profile count
SELECT COUNT(*) AS count FROM profiles;

-- Component count
SELECT COUNT(*) AS count FROM components;
```

### Sprints list — `GET /sprints`

```sql
SELECT * FROM sprints ORDER BY number DESC;
```

### Sprint detail — `GET /sprints/{id}`

```sql
-- Sprint
SELECT * FROM sprints WHERE id = ?;

-- Phase runs for this sprint
SELECT * FROM phase_runs WHERE sprint_id = ? ORDER BY iteration, attempt;

-- Dispatch logs for this sprint
SELECT * FROM dispatch_log WHERE sprint_id = ? ORDER BY id DESC;

-- Phase events for this sprint
SELECT * FROM phase_events WHERE sprint_id = ? ORDER BY id DESC LIMIT 50;
```

### Phase runs — `GET /phases`

```sql
SELECT pr.*, s.number AS sprint_number 
FROM phase_runs pr 
JOIN sprints s ON pr.sprint_id = s.id 
ORDER BY pr.id DESC;
```

### Dispatch log — `GET /dispatch`

```sql
SELECT * FROM dispatch_log ORDER BY id DESC;
```

### Profile list — `GET /profiles`

```sql
-- All profiles with component count
SELECT p.*, COUNT(pc.id) AS component_count
FROM profiles p
LEFT JOIN profile_components pc ON pc.profile_id = p.id
GROUP BY p.id
ORDER BY p.name;
```

### Profile detail — `GET /profiles/{id}`

```sql
-- Profile
SELECT * FROM profiles WHERE id = ?;

-- Components
SELECT c.*, pc.order_idx, pc.params 
FROM profile_components pc
JOIN components c ON c.id = pc.component_id
WHERE pc.profile_id = ?
ORDER BY pc.order_idx;

-- Pipeline state using this profile (if agent_name matches)
SELECT * FROM pipeline_states WHERE agent_name = (SELECT name FROM profiles WHERE id = ?);
```

## Template Structure

```
dashboard/templates/
├── base.html          # Layout with Bootstrap 5 nav, sidebar
├── home.html          # System status cards, recent runs, stats
├── sprints.html       # Sprint table
├── sprint_detail.html # Sprint info + phase runs + dispatch
├── phases.html        # Phase runs table
├── dispatch.html      # Dispatch log table
├── profiles.html      # Profile cards/table
└── profile_detail.html # Profile JSON + components
```

### base.html

Bootstrap 5 from CDN. Navbar with links to all 6 views. Sidebar or top nav. Content block.

### home.html

Four card sections:
1. **System Status** — active sprint badge, pipeline state count, profile count
2. **Recent Phase Runs** — table of last 10 runs
3. **Dispatch Stats** — pie-like stat boxes (pending, completed, failed)
4. **Phase Run Stats** — status breakdown

### sprints.html

Table: number, mode, status, started_at, completed_at. Status badges.

### sprint_detail.html

- Sprint info card
- Phase runs table (phase, iteration, attempt, status, duration)
- Dispatch log table (agent, status, created_at)
- Phase events timeline

### phases.html

Table: id, sprint number, phase, iteration, attempt, status, started_at, completed_at, output_summary (truncated).

### dispatch.html

Table: id, sprint_id, session_id, agent_name, status, created_at, completed_at, response_text (truncated).

### profiles.html

Card grid or table: name, version, header, component_count.

### profile_detail.html

- Profile metadata card
- Component assignments (ordered)
- Pipeline state assignment (if any)
- Raw header/permissions JSON view

## Data Flow

1. Request comes in → FastAPI route handler
2. Handler opens sqlite3 connection
3. Executes query, fetches results as dicts
4. Closes connection
5. Renders Jinja2 template with data
6. Response goes out

## Empty State Design

Every view must handle zero rows:
- "No sprints yet" with a muted icon
- "No phase runs recorded" 
- "No dispatch logs"
- Tables with empty-body rows showing a single "No data" cell with colspan

## Color Coding

Status badges:
- `active/running/pending` → `bg-primary`
- `completed/passed` → `bg-success`
- `failed` → `bg-danger`
- `planned` → `bg-secondary`
- `blocked` → `bg-warning text-dark`

---

*Specified by Saraswati. Built by Matsya. Watched by Kurma.*
