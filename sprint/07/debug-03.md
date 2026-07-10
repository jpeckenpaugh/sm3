# Debug 03: Three Issues From Vasuki's Test Run

*Observed by Kurma during Sprint 07 verification in `test-projects/test-3/`. None are Sprint 07 regressions — all are pre-existing structural gaps exposed by running from a fresh directory.*

---

## Issue 1 — `.opencode/tools/` Never Created by `sm init`

**Observed:** Vasuki ran `sm init` in `test-projects/test-3/`. The generated agent files declare tool permissions (`search_files: allow`, `lint_code: allow`, etc.), but the `.opencode/tools/` directory was never created and the tool definition files were never copied. When an agent tries to call `search_files`, the runtime finds no `.ts` file and fails silently.

### Root Cause

`cmd_init()` in `cli.py` creates these directories:

```python
for subdir in ["backlog", "sprint", ".opencode/agents", "scripts"]:
    os.makedirs(os.path.join(project_root, subdir), exist_ok=True)
```

It creates `.opencode/agents/` but **not** `.opencode/tools/`. The 7 tool definition files live at the project root at `/root/sm/.opencode/tools/` but are never copied into new projects.

### The Fix

1. Add `.opencode/tools` to the list of directories created by `cmd_init()`:

   ```python
   for subdir in ["backlog", "sprint", ".opencode/agents", ".opencode/tools", "scripts"]:
       os.makedirs(os.path.join(project_root, subdir), exist_ok=True)
   ```

2. After creating the directory structure, copy all `.ts` files from the source `.opencode/tools/` into the new project's `.opencode/tools/`:

   ```python
   # Source: the project's own tool definitions (resolved from package installation root)
   _SOURCE_TOOLS_DIR = _DEFAULT_SEED_ROOT / ".opencode/tools"
   # or from the running project root:
   # _SOURCE_TOOLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".opencode", "tools")
   
   target_tools_dir = os.path.join(project_root, ".opencode", "tools")
   source_tools_dir = os.path.join(_DEFAULT_SEED_ROOT, ".opencode", "tools")
   
   if os.path.isdir(source_tools_dir):
       import shutil
       for fname in os.listdir(source_tools_dir):
           if fname.endswith(".ts"):
               src = os.path.join(source_tools_dir, fname)
               dst = os.path.join(target_tools_dir, fname)
               if not os.path.isfile(dst):
                   shutil.copy2(src, dst)
                   print(f"  Tool: {fname}")
   ```

   This copies each `.ts` file into the new project only if it does not already exist (idempotent).

3. Print a confirmation line for each tool copied, same pattern as the existing script boilerplate output:

   ```
     Tool: search_files.ts
     Tool: list_files.ts
     Tool: file_tree.ts
     Tool: compare_files.ts
     Tool: lint_code.ts
     Tool: read_pulse.ts
     Tool: archive_features.ts
   ```

### Files to Change

| File | Change |
|------|--------|
| `src/genesis_sm/cli.py` `cmd_init()` | Add `.opencode/tools` to directory list. Add copy step after directory creation. |

---

## Issue 2 — `file_contracts` Duplicates on Re-Seed

**Observed:** Every call to `sm seed` inserts a fresh set of duplicate rows into `file_contracts`. After two seeds, the dispatch module sees doubled inputs and outputs:
```
POPULATE_BACKLOG INPUT1:concept.md INPUT2:concept.md OUTPUT1:backlog/ft-*.md OUTPUT2:backlog/ft-*.md
```

### Root Cause

The `file_contracts` table has no unique constraint:

```sql
CREATE TABLE IF NOT EXISTS file_contracts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    state_name  TEXT    NOT NULL,
    direction   TEXT    NOT NULL CHECK (direction IN ('input', 'output')),
    pattern     TEXT    NOT NULL,
    description TEXT    DEFAULT '',
    optional    INTEGER NOT NULL DEFAULT 0
);
```

The seed uses `INSERT OR IGNORE`, but `IGNORE` only skips insertion when a UNIQUE constraint would be violated. Since no constraint exists on `(state_name, direction, pattern)`, every insert succeeds.

### The Fix

1. Add a UNIQUE constraint to the `file_contracts` table in `schema.sql`:

   ```sql
   CREATE TABLE IF NOT EXISTS file_contracts (
       id          INTEGER PRIMARY KEY AUTOINCREMENT,
       state_name  TEXT    NOT NULL,
       direction   TEXT    NOT NULL CHECK (direction IN ('input', 'output')),
       pattern     TEXT    NOT NULL,
       template    TEXT    DEFAULT '',
       description TEXT    DEFAULT '',
       optional    INTEGER NOT NULL DEFAULT 0,
       UNIQUE(state_name, direction, pattern)
   );
   ```

2. In `pipeline/seeds.py`, change the insert to use `INSERT OR REPLACE` or add an explicit `ON CONFLICT` clause:

   ```python
   cursor.execute(
       """INSERT OR REPLACE INTO file_contracts
          (state_name, direction, pattern, template, description, optional)
          VALUES (?, ?, ?, ?, ?, ?)""",
       (state_name, direction, pattern, template, description, optional),
   )
   ```

   `INSERT OR REPLACE` matches on the UNIQUE constraint. If a row with the same `(state_name, direction, pattern)` exists, it is replaced with the new values. This makes re-seed idempotent.

3. After changing the schema, existing databases with duplicate rows need cleanup. Add a deduplication step in `seed_pipeline_tables()` or in `ensure_schema()`:

   ```python
   # Remove duplicates before inserting fresh data
   conn.execute("""
       DELETE FROM file_contracts
       WHERE id NOT IN (
           SELECT MIN(id) FROM file_contracts
           GROUP BY state_name, direction, pattern
       )
   """)
   ```

   This removes all duplicate rows, keeping only the first occurrence per unique combination.

### Files to Change

| File | Change |
|------|--------|
| `schema.sql` | Add `UNIQUE(state_name, direction, pattern)` to `file_contracts` table |
| `pipeline/seeds.py` | Change `INSERT OR IGNORE` to `INSERT OR REPLACE`. Add deduplication cleanup. |

---

## Issue 3 — Builder Permissions Too Restrictive for `src/**/*`

**Observed:** The builder's mode-specific component instructs the agent:

```
OUTPUT1: Source code files implementing all features (src/**/*)
```

But the builder's edit permissions deny most file types needed for full-stack implementation:

### Current Permissions

`profiles/builder.json` (base):
```json
"edit": {
    "*.py": "allow",
    "*.sh": "allow",
    "*.sql": "allow",
    "*.md": "allow"
}
```

`profiles/builder-ENGINEER.json` (derived, adds):
```json
"edit": {
    "*.txt": "allow",
    ".gitignore": "allow"
}
```

**Missing:** `*.html`, `*.js`, `*.css`, `*.ts`, `*.json`, `*.yaml`, `*.yml`, `*.jsx`, `*.tsx`, and any other file a feature implementation may produce.

### The Fix

Expand the builder's edit permissions to match the scope described in the mode-specific instructions. The permission should cover everything under `src/` that a feature implementation might produce.

Add to `profiles/builder.json` and/or `profiles/builder-ENGINEER.json`:

```json
"edit": {
    "*.py": "allow",
    "*.sh": "allow",
    "*.sql": "allow",
    "*.md": "allow",
    "*.txt": "allow",
    "*.html": "allow",
    "*.js": "allow",
    "*.css": "allow",
    "*.ts": "allow",
    "*.json": "allow",
    "*.yaml": "allow",
    "*.yml": "allow",
    ".gitignore": "allow"
}
```

The base `builder.json` should be the canonical home for these permissions so that all derived profiles (`builder-ENGINEER`, `builder-TEST`, `builder-FRONTEND`, etc.) inherit them automatically. Remove from derived profiles any extensions that are now covered by the base.

### Files to Change

| File | Change |
|------|--------|
| `profiles/builder.json` | Add missing web file extensions to `edit` permissions |
| `profiles/builder-ENGINEER.json` | Remove extensions now covered by base (`.txt`, `.gitignore`) — they will be inherited |
| `profiles/builder-TEST.json` | Review — may also inherit from base |

---

## Verification

### Issue 1 — Tools copied on init

```bash
rm -rf /tmp/test-tools
sm init /tmp/test-tools/matsya.db --yes
ls /tmp/test-tools/.opencode/tools/
# Expected: search_files.ts, list_files.ts, file_tree.ts, compare_files.ts,
#           lint_code.ts, read_pulse.ts, archive_features.ts
```

### Issue 2 — No duplicates on re-seed

```bash
rm -rf /tmp/test-contracts
sm init /tmp/test-contracts/matsya.db --yes
sm --db /tmp/test-contracts/matsya.db seed
# Expected: file_contracts table has unique (state_name, direction, pattern)
# No duplicate rows after second seed
```

### Issue 3 — Builder can write web files

```bash
# After re-seeding profiles
sm generate agent builder-ENGINEER
# Generated file should include *.html, *.js, *.css, *.ts, *.json, *.yaml
# in the edit permissions block
```

---

*Written by Saraswati, from Kurma's signal. Built by Matsya. Watched by Kurma.*
