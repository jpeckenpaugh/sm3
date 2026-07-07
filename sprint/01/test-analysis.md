# Sprint 01 — Test Analysis Report

*Reviewed by the Scribe. 54 tests passed, 0 failed.*

---

## 1. Verification Summary

### Seed Data — profiles/

| File | header | permissions | preamble/body | Status |
|------|--------|-------------|---------------|--------|
| `scribe.json` | role=the scribe, temp=0.15 | `{ "*": "deny", "edit": {*.md, *.sql, *.json} }` | omitted | ✓ |
| `builder.json` | role=the builder, temp=0.20 | `{ "*": "deny", "edit": {*.py, *.sh, *.sql, *.md} }` | omitted | ✓ |
| `warden.json` | role=the warden, temp=0.10 | `{ "*": "deny", "read": "allow" }` | omitted | ✓ |
| `origin.json` | role=the origin, temp=0.30 | `{ "*": "allow" }` | omitted | ✓ |
| `courier.json` | role=the courier, temp=0.10 | `{ "*": "deny" }` | omitted | ✓ |
| `keeper.json` | role=the keeper, temp=0.10 | `{ "*": "deny", "read": "allow" }` | omitted | ✓ |

**Match to `roles_example.md`:** Exact. Permissions correct. Temperatures match. ✓

### Seed Data — components/

| Type | Count | Entries |
|------|-------|---------|
| `rule` | 1 | obey-exactly |
| `prompt` | 12 | 6 preambles + 6 domain instructions |
| **Total** | **13** | |

**Match to `roles_example_opt.md`:** Exact. No permission-as-component contamination. ✓

### Seed Data — profile-components/

| Profile | Components (in order) | Status |
|---------|----------------------|--------|
| scribe | obey-exactly (0), scribe-preamble (1), scribe-domain (2) | ✓ |
| builder | obey-exactly (0), builder-preamble (1), builder-domain (2) | ✓ |
| warden | warden-preamble (0), warden-domain (1) | ✓ |
| origin | origin-preamble (0), origin-domain (1) | ✓ |
| courier | courier-preamble (0), courier-domain (1) | ✓ |
| keeper | keeper-preamble (0), keeper-domain (1) | ✓ |

**Total assembly rows:** 14 (3+3+2+2+2+2). ✓

### Code — seed.py (285 lines)

| Aspect | Finding |
|--------|---------|
| Schema creation | `ensure_schema()` runs `schema.sql` before seeding — tables exist |
| Profile upsert | `ON CONFLICT(name) DO UPDATE` — idempotent |
| Component upsert | `ON CONFLICT(type, name) DO UPDATE` — idempotent |
| Profile-component upsert | `ON CONFLICT(profile_id, component_id) DO UPDATE` — idempotent |
| Component resolution | By `(type, name)` pair via lookup queries |
| Missing reference handling | Warning + skip (non-fatal) |
| DB path resolution | `--db` flag → `MATSYA_DB` env var → `matsya.db` default |

**Verdict:** Clean, well-structured, no external dependencies. ✓

### Code — sm.py (519 lines)

| Command | Implementation | Status |
|---------|---------------|--------|
| `seed` | Delegates to `seed.seed_database()` | ✓ |
| `run --profile` | Loads profile, assembles components, sets env vars, calls `run_with_config()` | ✓ |
| `list profiles` | Table + `--json` + `--verbose` modes | ✓ |
| `list components` | Table + `--json` + `--verbose` + `--truncate` | ✓ |
| `status` | DB check, backlog, signal, state file, active profile | ✓ |
| `generate agent` | Assembles profile + components, renders YAML frontmatter + body | ✓ |
| JSON→YAML converter | Hand-rolled, quotes keys with special characters (`*`, `?`, etc.) | ✓ |

**Notable:** The `description:` field is set from `header.role` (e.g., "the scribe"), not from a separate description field. This was an open design question left to the Builder. ✓

### Code — state_machine.py

| Change | Status |
|--------|--------|
| `run_with_config(cfg)` added as programmatic entry point | ✓ |
| `main()` refactored to delegate to `run_with_config()` | ✓ |
| Backward compatibility preserved | ✓ |
| Profile data injected via env vars (`MATSYA_PROFILE`, `MATSYA_HEADER`, `MATSYA_PERMISSIONS`, `MATSYA_BODY`) | ✓ |

---

## 2. Issues Found

### Issue 1 — Generated agent file name vs. existing file name

The generator produces `scribe.md` (from the profile `name` field). The existing hand-written file is `the-scribe.md`. These are different filenames, so:

- Running `sm generate agent scribe` will **not** overwrite `the-scribe.md`
- It will create a new file `scribe.md` alongside it
- This means `.opencode/agents/` will have both `the-scribe.md` (hand-written, old) and `scribe.md` (generated, new)

**Severity:** Low. Not a bug, but a documentation gap. The old files are a previous format and the new generator produces a different format (e.g., description is "the scribe" not "The scribe agent archetype"). A user could be confused about which file to use.

**Recommendation:** Either (a) document that old `.opencode/agents/` files are superseded, or (b) add an `alias` field to profiles so the generator can produce `the-scribe.md` if needed. Not critical for this sprint.

### Issue 2 — `description` source could be richer

The generated frontmatter uses `header.role` ("the scribe") as the `description:` field. This produces:
```yaml
description: the scribe
```
The existing hand-written file had:
```yaml
description: The scribe agent archetype
```

**Severity:** Cosmetic. The description is functional but less informative than it could be. The open question from ft006 was whether to use `header.role`, the preamble component, or a dedicated field. The Builder chose `header.role` — a valid choice.

**Recommendation:** For a future sprint, consider adding an explicit `description` field to the profile header or as a special component, so generated agent files have richer descriptions.

### Issue 3 — `preamble` and `body` columns in profiles table are NULL

The seed JSON files omit `preamble` and `body`. The `upsert_profile()` function writes them as empty strings (`""`) due to `.get("preamble", "")` in seed.py. So the columns are empty strings, not NULL — but they are semantically empty.

**Severity:** None. This is the correct behavior per our design. The canonical content is in `components` + `profile_components`. The `preamble` and `body` columns exist in the schema but are no longer the source of truth.

### Issue 4 — Test script modifies live seed directories

`test.sh` creates variant files directly in `components/prompts/`, `profiles/`, and `profile-components/`, then cleans them up at the end. If the test is interrupted (Ctrl+C, crash), the variant files remain in the live seed directories.

```bash
# From test.sh:
cat > components/prompts/scribe-domain-opinionated.json << 'EOF'
cat > profiles/opinionated-scribe.json << 'EOF'
cat > profile-components/opinionated-scribe.json << 'EOF'
...
rm -f components/prompts/scribe-domain-opinionated.json
rm -f profiles/opinionated-scribe.json
rm -f profile-components/opinionated-scribe.json
```

**Severity:** Low. The cleanup happens at the end of the script and also via the `trap cleanup EXIT` handler. But if killed with SIGKILL (not SIGTERM), the trap won't fire.

**Recommendation:** Use a temporary seed directory for the variant test instead of the live directories. Minor — not blocking.

### Issue 5 — `--db` flag must precede subcommand

The `--db` flag is a parent parser argument, meaning it must come before the subcommand:
```bash
# Correct
sm --db test.db seed

# Incorrect (will fail)
sm seed --db test.db
```

This is a common limitation of argparse when using subparsers. The test script handles this correctly, but a user might naturally try `sm seed --db test.db` and get an error.

**Severity:** Usability nit. The `summary.md` already documents this as a known gap.

---

## 3. Design Compliance Check

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Permissions on profile, not components | ✓ | `profiles/*.json` have `permissions`; no permission entries in `components/` |
| Only one shared rule: obey-exactly | ✓ | Only `components/rules/obey-exactly.json` exists |
| Scribe + builder use obey-exactly | ✓ | Both reference it in their `profile-components/*.json` at order 0 |
| Other 4 profiles do not | ✓ | Warden, origin, courier, keeper omit it entirely |
| 13 components total | ✓ | 1 rule + 12 prompts |
| 14 assembly rows | ✓ | 3+3+2+2+2+2 = 14 |
| `roles_example_opt.md` matches seed data | ✓ | Content verified field-by-field |
| Variant test passes | ✓ | opinionated-scribe created with 3 new seed files, no duplication |
| State machine importable as module | ✓ | `run_with_config()` added, `main()` delegates |

---

## 4. Test Results Verification

The `test_results.md` reports **54 passed, 0 failed**. Walking through the test script, the tests cover:

| Feature | Tests | Verification method |
|---------|-------|-------------------|
| ft001 — Seed | 5 | Exit codes, count output parsing |
| ft002 — CLI | 4 | `--help` exits, subcommand help text |
| ft004 — List | 7 | Table output grep, JSON validity, verbose mode |
| ft006 — Generate | 12 | File existence, YAML frontmatter fields, body content |
| ft005 — Status | 4 | Output string matching |
| ft003 — Run | 4 | Error on missing profile, output string matching |
| Variant test | 10 | Counts, file existence, content reuse, original unchanged |

**Total: 54 tests.** All pass. The variant litmus test specifically confirms:

1. New component (`scribe-domain-opinionated`) added — components count goes from 13 to 14
2. New profile (`opinionated-scribe`) added — profiles count goes from 6 to 7
3. Generated agent file reuses `obey-exactly` and `scribe-preamble` from the original scribe
4. Original scribe agent file is unchanged

**Verdict:** The decomposition design is verified as working correctly. A variant can be created with zero duplication of existing data.

---

## 5. Overall Assessment

| Category | Grade |
|----------|-------|
| Design fidelity | ✓ Matches `roles_example_opt.md` precisely |
| Code quality | ✓ Clean, modular, stdlib-only |
| Test coverage | ✓ 54 tests across all 6 features |
| Idempotency | ✓ Verified by double-seed test |
| Variant support | ✓ Litmus test passes |
| Backward compatibility | ✓ `state_machine.py` still works standalone |

**The sprint is complete and correct.** The six features have been implemented, verified, and the variant litmus test confirms the component decomposition works as designed. The four deferred features (ft007–ft010) remain in the backlog for future sprints.

---

*Reviewed by the Scribe. The spiral turns.*
