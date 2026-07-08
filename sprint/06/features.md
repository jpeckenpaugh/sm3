# Sprint 06 — Features

*Close out the backlog. Four features, one cleanup, zero debt remaining.*

---

| # | Feature | Source | Depends on |
|---|---------|--------|------------|
| 1 | **ft009 — Component params override** | `backlog/ft009` | — |
| 2 | **ft008 — Variant creation workflow** | `backlog/ft008` | ft009 |
| 3 | **ft017 — Webbfetch proxy** | `backlog/ft017` | — |
| 4 | **ft010 — Profile export/import** | `backlog/ft010` | — |
| 5 | **Fix ft007 duplicate numbering** | backlog artifact | — |
| 6 | **End-to-end verification** | All features | 1–5 |

---

## Dependency Rationale

### Step 1 — Component params (ft009)

The `params` column on `profile_components` has been in the schema since Sprint 01 but was never wired into the generation pipeline. This step completes it:

In `_assemble_components_for_profiles()` in `cli.py`, after fetching component content, apply param substitution:

```python
import re

def _apply_params(content, params):
    """Replace {{ key }} placeholders with param values."""
    if not params:
        return content
    for key, value in params.items():
        content = content.replace("{{ " + key + " }}", str(value))
        content = content.replace("{{" + key + "}}", str(value))
    return content
```

Update the generator to pass params from `profile_components` through this function.

### Step 2 — Variant creation (ft008)

New CLI subcommand `sm profile variant`:

```bash
sm profile variant --base <base_name> --name <new_name> \
  --mode <mode_flag> \
  --prompt "<mode-specific instructions>" \
  [--params '{"key": "value"}']
```

What it does:
1. Validates the base profile exists in the database
2. Creates a new profile row with `name = <new_name>`, `base_profile = <base_name>`, header/permissions inherited from base
3. Creates a new component row with `type: prompt, name: <base_name>-mode-<mode_flag_lower>`
4. Links them via `profile_components`
5. Generates the agent file
6. Prints: `✓ Variant <new_name> created. Agent file: .opencode/agents/<new_name>.md`

The `--params` flag stores JSON in the `profile_components.params` column (depends on ft009).

### Step 3 — Webbfetch proxy (ft017)

A lightweight proxy at `scripts/proxy.py` (stdlib `http.server` or `FastAPI`):

```python
# scripts/proxy.py — Domain-filtered webfetch proxy
"""Start with: python3 scripts/proxy.py [--port 8080] [--allow-list proxy-allow-list.json]"""
```

The proxy:
- Listens on a local port (default 8080)
- Accepts POST requests with `{"url": "https://docs.python.org/3/library/os.html"}`
- Checks the URL's domain against the allow list
- If allowed, fetches the URL and returns the content
- If denied, returns 403 with `{"error": "Domain not allowed"}`
- Logs all requests to stdout

The allow list at `scripts/proxy-allow-list.json`:

```json
{
  "allowed_domains": [
    "docs.python.org",
    "pypi.org",
    "fastapi.tiangolo.com",
    "opencode.ai",
    "raw.githubusercontent.com"
  ],
  "allowed_prefixes": [
    "https://docs.python.org/",
    "https://pypi.org/"
  ]
}
```

No agent profile changes needed — the proxy is transparent to agents. They call `webfetch` with the proxy's URL and the target as a parameter.

### Step 4 — Profile export/import (ft010)

Two new CLI subcommands:

```bash
sm profile export --output profiles-export.json
sm profile import --input profiles-export.json
```

Export writes a JSON file containing all profiles, components, and profile_components:

```json
{
  "profiles": [
    {
      "name": "scribe-PLAN",
      "version": "1.0.0",
      "header": {...},
      "permissions": {...},
      "base_profile": "scribe"
    }
  ],
  "components": [...],
  "profile_components": [...],
  "exported_at": "2026-07-08T..."
}
```

Import reads the file and upserts each entity (matched on name for profiles, (type, name) for components, (profile_id, component_id) for profile_components).

Import is idempotent — safe to run multiple times against the same database.

### Step 5 — Fix ft007 duplicate numbering

Two files share `ft007`:
- `backlog/ft007-check-syntax-tool.md`
- `backlog/ft007b-profile-inheritance.md`

Rename: `ft007-profile-inheritance.md` → `ft007b-profile-inheritance.md` (done). Update any cross-references.

### Step 6 — End-to-end verification

```bash
# 1. Component params
bash sprint/06/test-params.sh

# 2. Variant creation
sm profile variant --base builder --name builder-FRONTEND \
  --mode FRONTEND --prompt "Build UI components"
sm generate agent builder-FRONTEND
ls .opencode/agents/builder-FRONTEND.md  # should exist

# 3. Webbfetch proxy
python3 scripts/proxy.py &  # start proxy
# Test allowed domain
curl -X POST -d '{"url":"https://docs.python.org/3/"}' http://localhost:8080/
# Test denied domain
curl -X POST -d '{"url":"https://example.com"}' http://localhost:8080/
# Should return 403

# 4. Export/import
sm profile export --output /tmp/profiles-test.json
python3 -m genesis_sm.seed  # reset DB
sm profile import --input /tmp/profiles-test.json
sm generate agents  # verify import worked
```

---

## Build Order Diagram

```
1. ft009 (params) ──────┐
                        ├──► 2. ft008 (variant)
3. ft017 (proxy) ───────┤
                        ├──► 5. ft007 fix ──► 6. Verify
4. ft010 (export) ──────┘
```

---

## Reference Documents

- `backlog/ft008-variant-creation-workflow.md`
- `backlog/ft009-component-params-override-system.md`
- `backlog/ft010-profile-export-import.md`
- `backlog/ft017-webfetch-proxy.md`
- `sprint/06/brief.md`

---

*Written by Saraswati. Built by Matsya. Watched by Kurma. The backlog ends here.*
