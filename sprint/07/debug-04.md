# Debug 04: Custom Tools Never Tested

*All seven `.opencode/tools/*.ts` files were written in Sprint 05 and merged as complete, but none were ever run. Every one of them has bugs that cause them to fail.*

---

## Common Pattern

Each `.ts` file:
1. Builds a shell command string
2. Passes it to `const result = await Bun.$`${cmd}`.text();`
3. The backing script in `scripts/` has quoting, parsing, or logic errors

---

## Bug 1 — `search_files.ts` / `search_files.sh`

**File:** `.opencode/tools/search_files.ts`, `scripts/search_files.sh`

**Root cause:** The shell script wraps `--include` value in literal single quotes, and uses `eval` with unquoted variable expansion.

**Line 38 of search_files.sh:**
```bash
GREP_OPTS="$GREP_OPTS --include='$INCLUDE'"
# Produces: -r -n -F --include='*.py'
```

The single quotes are literal characters, not shell syntax. When `eval` executes this on line 41:

```bash
RESULTS=$(eval grep $GREP_OPTS "$PATTERN" "$ROOT" 2>/dev/null)
```

`grep` receives `--include='*.py'` as a single argument with literal quote marks. It either ignores the pattern or fails to match.

**Fix:** Remove the single quotes. The shell variable expansion provides quoting:

```bash
GREP_OPTS="$GREP_OPTS --include=$INCLUDE"
```

Since the whole expression is inside `eval`, word splitting already protects the argument. Or better, avoid `eval` entirely and use array-based argument construction.

---

## Bug 2 — `read_pulse.ts` / `read_pulse.sh`

**File:** `.opencode/tools/read_pulse.ts`, `scripts/read_pulse.sh`

**Root cause:** The SQL query references `phase_events` table with column `created_at` which may not exist or has a different schema. The script silently exits with code 1.

**Line 42-43 of read_pulse.sh:**
```sql
(SELECT json_object('timestamp', created_at, 'event_type', event_type, 'status', 'active')
 FROM phase_events ORDER BY id DESC LIMIT 1) AS last_pulse,
```

If the `phase_events` table has different column names, or if the `sqlite3 -json` command fails, the entire script fails. The `2>/dev/null` on the sqlite3 call hides the error.

**Fix:** Replace the fragile subquery with a simpler query that handles missing tables gracefully. Use `sqlite3` without `-json` flag and parse manually, or wrap in `IFNULL` / `CASE`:

```sql
SELECT
  (SELECT COUNT(*) FROM sprints) AS sprint_count,
  (SELECT COUNT(*) FROM phase_runs) AS phase_count,
  (SELECT MAX(completed_at) FROM phase_runs) AS last_pulse_at,
  (SELECT number FROM sprints ORDER BY id DESC LIMIT 1) AS last_sprint,
  (SELECT status FROM sprints ORDER BY id DESC LIMIT 1) AS last_sprint_status
```

Remove the dependency on `phase_events` table entirely — the pulse check ritual only needs sprints and phase_runs.

---

## Bug 3 — `list_files.ts` / `list_files.sh`

**File:** `.opencode/tools/list_files.ts`, `scripts/list_files.sh`

**Root cause:** Two issues:

**Issue A — JSON output contains trailing content after the loop.**

Lines 38-50 construct JSON by echoing line by line. After the `while read` loop, line 49 has a bare `echo ''` that injects an empty string into the output, breaking JSON parsing for the tool consumer.

**Issue B — `find -path` with `./` prefix on bare patterns.**

Line 28:
```bash
RESULTS=$(find . -path "./$PATTERN" -type f 2>/dev/null | head -n "$MAX")
```

If `PATTERN` is `backlog/*.md`, this works. But if `PATTERN` is a simple filename like `config.json`, `-path "./config.json"` only matches files literally at the root, not nested paths. Expected behavior is to find any file matching the name.

**Fix:**
```bash
# Try direct glob first, fall back to name matching
RESULTS=$(find . -path "./$PATTERN" -type f 2>/dev/null | head -n "$MAX")
if [ -z "$RESULTS" ]; then
    RESULTS=$(find . -name "$PATTERN" -type f 2>/dev/null | head -n "$MAX")
fi
```

And rebuild the JSON output to avoid trailing empty lines.

---

## Bug 4 — `file_tree.ts` / `file_tree.sh`

**File:** `.opencode/tools/file_tree.ts`, `scripts/file_tree.sh`

**Root cause:** Output is not parseable JSON. The script uses `tree` or `find` output directly (plain text), but the tool's description and agent expectations imply structured output.

**Line 28-35:**
```bash
if command -v tree &> /dev/null; then
    eval tree $TREE_OPTS 2>/dev/null
else
    find . -maxdepth "$DEPTH" ...
fi
```

The `tree` command outputs ANSI box-drawing characters. The `eval` on line 35 also has quoting issues similar to Bug 1 — the `-P '$PATTERN'` wraps the pattern in literal single quotes.

**Fix:** Add `-J` flag for JSON output if `tree` supports it, or wrap the output in a JSON structure:

```bash
if command -v tree &> /dev/null; then
    tree -J -L "$DEPTH" 2>/dev/null
else
    # ... fallback producing JSON
fi
```

---

## Bug 5 — `compare_files.ts` / `compare_files.sh`

**File:** `.opencode/tools/compare_files.ts`, `scripts/compare_files.sh`

**Root cause:** The hunk count defaults to 1 even when there are 0 hunks.

**Line 43:**
```bash
HUNKS=$(echo "$DIFF_OUT" | grep -c '^@@' || echo "1")
```

`grep -c` returns exit code 1 when no match is found (0 matches). The `|| echo "1"` fires, setting HUNKS=1 even when the files have no hunks because they just differ in header lines.

**Fix:** Remove the `||` fallback. `grep -c` already produces the correct number (0) on stdout:

```bash
HUNKS=$(echo "$DIFF_OUT" | grep -c '^@@' || true)
```

---

## Bug 6 — `lint_code.ts` / `lint_code.sh`

**File:** `.opencode/tools/lint_code.ts`, `scripts/lint_code.sh`

**Root cause:** The pyflakes output parser splits on `:` but the error code and message are in the same field.

**Line 37:**
```bash
while IFS=: read -r FILE LINE COL TYPE REST; do
```

For pyflakes output `file.py:42:5: F821 undefined name 'foo'`:
- FILE = file.py
- LINE = 42
- COL = 5
- TYPE =  F821 undefined name 'foo'  (includes the message)
- REST = (empty)

The case statement on line 44:
```bash
case "$TYPE" in
    F821|F822|...) SEVERITY="error" ;;
```

Never matches because `$TYPE` is `' F821 undefined name 'foo''`, not `'F821'`.

Also, the error/warning/style counts on lines 52-54 are hardcoded to 0, never computed.

**Fix:** Parse pyflakes output differently. Extract the error code separately:

```bash
while IFS=: read -r FILE LINE COL MSG; do
    CODE=$(echo "$MSG" | awk '{print $1}')
    MESSAGE=$(echo "$MSG" | sed 's/^[[:space:]]*[A-Z0-9]* //')
    # ... use $CODE for the case statement
done
```

---

## Bug 7 — `archive_features.ts` / `archive_features.sh`

**File:** `.opencode/tools/archive_features.ts`, `scripts/archive_features.sh`

**Root cause:** The TypeScript file does not pass the sprint number correctly.

**Line 15 of archive_features.ts:**
```ts
const result = await Bun.$`bash ${scriptPath} ${args.sprintNum}`.text();
```

This uses `Bun.$` template literal interpolation. If `args.sprintNum` is a number like `3`, it works. But the tool description says the format is `"001"` (zero-padded). The TypeScript does no padding. If the caller passes `3`, the shell script looks for `sprint/3/features/` which doesn't exist — directories are `sprint/03/`.

The shell script itself (line 29) handles missing directories gracefully:
```bash
if [ ! -d "$SPRINT_FEATURES_DIR" ]; then
    echo "No features directory found — nothing to archive."
    exit 0
fi
```

So the bug is subtle: the tool silently does nothing because the directory doesn't match.

**Fix:** Pad the sprint number in the TypeScript:

```ts
const sprintNum = String(args.sprintNum).padStart(2, '0');
const result = await Bun.$`bash ${scriptPath} ${sprintNum}`.text();
```

Or handle unpadded numbers in the shell script:
```bash
SPRINT_NUM=$(printf "%02d" "$1" 2>/dev/null || echo "$1")
```

---

## Summary

| Tool | Severity | Root Cause |
|------|----------|------------|
| `search_files` | 🔴 Fails on any `--include` flag | Literal quotes in grep option |
| `read_pulse` | 🔴 Fails if phase_events table missing | Brittle SQL with no fallback |
| `list_files` | 🟡 Produces broken JSON | Trailing echo in JSON output |
| `file_tree` | 🟡 Output not parseable | Plain text instead of JSON |
| `compare_files` | 🟡 Hunk count always ≥1 | `grep -c || echo "1"` off-by-one |
| `lint_code` | 🔴 Error codes never match | Wrong field splitting for pyflakes |
| `archive_features` | 🟡 Sprint padding mismatch | No zero-padding on sprint number |

---

## Files to Change

| File | Bug |
|------|-----|
| `scripts/search_files.sh` line 38 | Remove literal quotes around `$INCLUDE` |
| `scripts/read_pulse.sh` lines 37-46 | Replace `phase_events` query with `phase_runs` / `sprints` queries |
| `scripts/list_files.sh` line 49 | Remove bare `echo ''` after the loop |
| `scripts/list_files.sh` line 28 | Add fallback for simple name patterns |
| `scripts/file_tree.sh` line 35 | Add `-J` flag for JSON output |
| `scripts/file_tree.sh` line 33 | Remove literal quotes around pattern |
| `scripts/compare_files.sh` line 43 | Remove `|| echo "1"` fallback, replace with `|| true` |
| `scripts/lint_code.sh` lines 37-45 | Parse error code and message separately |
| `scripts/lint_code.sh` lines 52-54 | Compute actual counts |
| `.opencode/tools/archive_features.ts` line 15 | Pad sprint number to 2 digits |

---

*Written by Saraswati, after testing every tool and watching every one fail. Built by Matsya. Tested by no one before now.*
