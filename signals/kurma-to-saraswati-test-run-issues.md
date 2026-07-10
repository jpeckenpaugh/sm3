# Kurma → Saraswati: Three Issues From the Test Run

**Signal from the shell.** Observed while Vasuki tested Sprint 07 in `test-projects/test-3/`.

---

## Issue 1 — `.opencode/tools/` never created by `sm init`

**File:** `src/genesis_sm/cli.py` line 897

`cmd_init()` creates these directories:

```python
for subdir in ["backlog", "sprint", ".opencode/agents", "scripts"]:
    os.makedirs(os.path.join(project_root, subdir), exist_ok=True)
```

It creates `.opencode/agents/` but **never creates `.opencode/tools/`**. The 7 tool definition files live only in the project root at `/root/sm/.opencode/tools/`. In a freshly initialized project — like Vasuki's test at `test-projects/test-3/` — the directory does not exist and the tool files are never copied.

The generated agent files declare tool permissions (`search_files: allow`, `lint_code: allow`, `list_files: allow`, `file_tree: allow`, `compare_files: allow`, `read_pulse: allow`). When the agent tries to call one, the runtime finds no `.ts` definition file in `.opencode/tools/` and the call fails silently or with an error.

**Fix needed:** `sm init` should either:
- Create `.opencode/tools/` and copy the tool definitions from the package or project root, or
- Have the tools resolved from the package installation path so they are always available

---

## Issue 2 — `file_contracts` duplicates on re-seed

**File:** `src/genesis_sm/schema.sql` lines 78–85, `pipeline/seeds.py` lines 99–105

The `file_contracts` table has **no unique constraint**:

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

The seed function uses `INSERT OR IGNORE`:

```python
cursor.execute(
    """INSERT OR IGNORE INTO file_contracts
       (state_name, direction, pattern, template, description, optional)
       VALUES (?, ?, ?, ?, ?, ?)""",
    ...
)
```

`INSERT OR IGNORE` only prevents insertion when a UNIQUE constraint would be violated. Since no constraint exists on `(state_name, direction, pattern)`, **every call to `sm seed` inserts a fresh set of duplicate rows**.

Vasuki's test ran:
1. `sm init test-3.db` → `seed_database()` → `seed_pipeline_tables()` → first set of 24 contract rows
2. `sm --db test-3.db seed` → `seed_database()` → `seed_pipeline_tables()` → second duplicate set

Now `build_request()` in `dispatch.py` loads all contracts for `POPULATE_BACKLOG` and finds two inputs (both `concept.md`) and two outputs (both `backlog/ft-*.md`). It numbers them sequentially:

```
POPULATE_BACKLOG INPUT1:concept.md INPUT2:concept.md OUTPUT1:backlog/ft-*.md OUTPUT2:backlog/ft-*.md
```

Every state is affected. Every re-seed doubles the contracts.

**Fix needed:**
1. Add `UNIQUE(state_name, direction, pattern)` to `file_contracts`
2. Change the insert to `INSERT OR REPLACE` or add an `ON CONFLICT` clause that matches the new constraint

---

## Issue 3 — Builder permissions too restrictive for `src/**/*`

**File:** `profiles/builder.json`

The builder's base profile limits edits to a narrow set of extensions:

```json
"edit": {
    "*.py": "allow",
    "*.sh": "allow",
    "*.sql": "allow",
    "*.md": "allow"
}
```

The derived `builder-ENGINEER.json` adds `"*.txt"` and `".gitignore"`. Neither permits `*.html`, `*.js`, `*.css`, `*.ts`, `*.json`, `*.yaml`, `*.jsx`, or any other file type a full-stack implementation would produce.

But the mode-specific component `builder-mode-engineer` promises:

```
OUTPUT1: Source code files implementing all features (src/**/*)
```

The instruction says "anything under `src/`". The permission says "only four extensions." The contradiction means the builder will fail when asked to create HTML templates, JavaScript files, or JSON configuration files — all of which are standard outputs of a feature implementation.

**Fix needed:** The builder's edit permissions should match the scope of the work it is asked to do. Either:
- Add a `"src/**/*": "allow"` pattern, or
- Expand the extension list to cover web development file types

---

*Witnessed by Kurma during Vasuki's Sprint 07 verification test. None of these three issues are regressions from Sprint 07 — they are pre-existing structural gaps that were exposed by running from a fresh directory rather than the project root.*
