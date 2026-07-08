# Sprint 06 — Profile Power Tools

*The clean-up sprint. Close out the remaining backlog. Give the pantheon web reach, variant power, override depth, and cross-container portability.*

---

## The Context

Sprint 05 gave the pantheon tools — search, discover, orient, compare, lint, pulse. The profiles were cleaned up, the zombie columns removed, the permissions merged. The engine runs cleanly, linearly, and observably.

What remains in the backlog are four features from earlier sprints — deferred because they were not blocking, but now they are the last unfinished work:

- **ft017 — Webbfetch proxy:** Agents need web access. Currently webfetch is all-or-nothing. A proxy gives domain-filtered access.
- **ft009 — Component params override:** The `params` column exists but the generator doesn't resolve it. Overrides at composition time.
- **ft008 — Variant creation workflow:** A CLI command to create derived profiles dynamically — `sm profile variant`.
- **ft010 — Profile export/import:** Share profiles between containers as JSON.

And one artifact: **ft007** has a duplicate file number (two files share ft007). Clean that up.

---

## The Features

### ft017 — Webbfetch Proxy

A lightweight proxy server that sits between agents and the web. Agents send requests to the proxy with a target URL; the proxy checks the domain against an allowed list and either forwards the request or denies it.

The proxy is a FastAPI or stdlib-http server, runnable with a single command. The allowed-list is a simple JSON config file:

```json
{
  "allowed_domains": [
    "docs.python.org",
    "pypi.org",
    "fastapi.tiangolo.com",
    "opencode.ai"
  ]
}
```

Agents call `webfetch` as before — the proxy is transparent to them. The filtering happens at the network boundary, not in the agent profile.

**Key files:** `scripts/proxy.py`, `.opencode/tools/webfetch_proxy.ts` (or just `proxy_start.sh`)

---

### ft009 — Component Params Override

The `profile_components` table has a `params TEXT DEFAULT '{}'` column. Seed data already populates it in some cases. The generator (`_assemble_components_for_profiles()`) currently ignores it.

The fix: when a `profile_components` entry has non-empty `params`, merge those params into the component content before rendering. Params use a simple `{{ key }}` template syntax within the component content:

```
Content: "In {{ mode }} mode, you read the provided INPUT files."
Params:  { "mode": "PLAN" }
Result:  "In PLAN mode, you read the provided INPUT files."
```

This allows mode-specific components to be fully generic — the mode name, input paths, and output paths are injected at composition time rather than hardcoded.

**Key files:** `src/genesis_sm/cli.py` (`_assemble_components_for_profiles`), `profile-components/*.json`

---

### ft008 — Variant Creation Workflow

A new CLI command: `sm profile variant` that creates a new derived profile from an existing base:

```bash
sm profile variant --base builder --name builder-FRONTEND \
  --mode FRONTEND \
  --prompt "In FRONTEND mode, you build UI components..."
```

The command:
1. Creates a new `profiles` row with `base_profile: builder` and `name: builder-FRONTEND`
2. Creates a new `components` row with `type: prompt, name: builder-mode-frontend` and the given prompt content
3. Links them via `profile_components`
4. Generates the agent file via `sm generate agent builder-FRONTEND`
5. Prints the path to the new agent file

Optional `--params` flag for passing component params at variant creation time (depends on ft009).

**Key files:** `src/genesis_sm/cli.py` (new `cmd_profile_variant` function)

---

### ft010 — Profile Export/Import

Two commands:

```bash
# Export all profiles to a JSON file
sm profile export --output profiles-export.json

# Import profiles from a JSON file (idempotent — upserts by name)
sm profile import --input profiles-export.json
```

The export format is a JSON array of profile objects — name, version, header, permissions, base_profile. Components and profile_components are included as nested arrays. The import command reads the file and upserts each profile, component, and profile-component link.

This enables sharing profiles between containers — the child container's profiles could be exported and imported here, and vice versa.

**Key files:** `src/genesis_sm/cli.py` (new `cmd_profile_export`, `cmd_profile_import`)

---

## Build Order

| Step | Feature | Depends on |
|------|---------|------------|
| 1 | **ft009 — Component params** | — |
| 2 | **ft008 — Variant creation** | ft009 |
| 3 | **ft017 — Webbfetch proxy** | — |
| 4 | **ft010 — Profile export/import** | — |
| 5 | **Fix ft007 duplicate numbering** | — |
| 6 | **End-to-end verification** | All above |

Steps 1, 3, and 4 are independent and can be built in parallel. Step 2 depends on step 1.

---

## What This Completes

After Sprint 06, the backlog will be empty. Every feature from Sprint 0 through Sprint 05 will be implemented. The engine, the pipeline, the tools, the profiles, the dashboard, the cleanup — all of it delivered.

The backlog will be clean for the first time since the experiment began. The next sprint can start from a fresh concept rather than from accumulated debt.

---

*Written by Saraswati. Built by Matsya. Watched by Kurma.*
