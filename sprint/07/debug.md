# Debug: Seed Root Default Resolution

*Found by Kurma during Sprint 07 testing. A structural gap inherited from Sprint 05's packaging migration.*

---

## The Bug

When `sm init <db_path>` or `sm seed` is run from outside the project root directory, the seed data (`profiles/`, `components/`, `profile-components/`) cannot be found. The commands silently produce an empty database with no agent profiles.

### Example

```bash
cd /tmp
sm init test.db --yes
# Database created, but no profiles loaded:
# "No seed directories found (profiles/, components/, profile-components/)"
```

### Root Cause

Three locations all default `--seed-root` to `"."` (the current working directory):

| Location | Line |
|----------|------|
| `cli.py` — `init` subparser | `p_init.add_argument("--seed-root", default=".", ...)` |
| `cli.py` — `seed` subparser | `p_seed.add_argument("--seed-root", default=".", ...)` |
| `seed.py` — `seed_database()` | `seed_root = seed_root or "."` |
| `seed.py` — `main()` CLI | `parser.add_argument("--seed-root", default=".", ...)` |

In the legacy `sm.py`, seed paths were resolved relative to the script itself:

```python
SM_DIR = os.path.dirname(os.path.abspath(__file__))
# sm.py lived at the project root → seed data found correctly
```

After the Sprint 05 packaging migration, `cli.py` moved to `src/genesis_sm/cli.py`. The `__file__` approach no longer works because the script location (`src/genesis_sm/`) is not where the seed data lives (project root). The default was changed to `"."` as a stopgap, but this breaks when CWD ≠ project root.

---

## Where the Seed Data Lives

```
/root/sm/                          ← project root (seed root)
├── profiles/
│   ├── scribe.json
│   ├── builder.json
│   └── ...
├── components/
│   ├── rules/
│   └── prompts/
├── profile-components/
│   └── ...
├── src/
│   └── genesis_sm/
│       ├── cli.py                  ← __file__ is here
│       ├── seed.py                 ← __file__ is here
│       └── generator.py
```

The seed root is **two directories up** from `cli.py` and `seed.py`.

---

## The Fix

### 1. Compute a package-relative default seed root

In both `cli.py` and `seed.py`, add a constant that resolves the project root from the package location:

```python
# At module level, after the existing imports and constants:
_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_SEED_ROOT = os.path.normpath(os.path.join(_PACKAGE_DIR, "..", ".."))
# For a dev install:  src/genesis_sm/../../  →  project root
# For a site-packages install: falls back gracefully if seed dirs not found
```

### 2. Update argument defaults

In `cli.py` `build_parser()`:

```python
# Line 1447 — init subparser
p_init.add_argument("--seed-root", default=_DEFAULT_SEED_ROOT,
    help="Root directory containing seed data (default: relative to package)")

# Line ~1576 — seed subparser  
p_seed.add_argument("--seed-root", default=_DEFAULT_SEED_ROOT,
    help="Root directory containing seed data (default: relative to package)")
```

In `seed.py` `seed_database()`:

```python
def seed_database(db_path=None, schema_path=None, seed_root=None):
    ...
    seed_root = seed_root or _DEFAULT_SEED_ROOT
```

In `seed.py` `main()`:

```python
parser.add_argument("--seed-root", default=_DEFAULT_SEED_ROOT,
    help="Root directory containing seed data")
```

### 3. Add a guard in `seed_database()`

The function already checks if seed directories exist and returns exit code 1 if not (line 298–300). But it should also print a helpful message pointing to `--seed-root`:

```python
if not seed_dirs_exist:
    print(f"  ✗ No seed directories found in '{seed_root}'")
    print(f"    Run with --seed-root <path> pointing to profiles/, components/, profile-components/")
    return 1
```

---

## Verification

```bash
# Test 1: Run from project root (must still work)
cd /root/sm
python3 -m genesis_sm.cli init /tmp/test1/matsya.db --yes
# Expected: profiles loaded, 16 agents generated

# Test 2: Run from outside project root (the bug)
cd /tmp
python3 -m genesis_sm.cli init /tmp/test2/matsya.db --yes \
    --schema /root/sm/schema.sql
# Expected: profiles loaded, not "No seed directories found"

# Test 3: Explicit --seed-root still overrides
cd /tmp
python3 -m genesis_sm.cli init /tmp/test3/matsya.db --yes \
    --seed-root /some/other/seed-data
# Expected: uses provided seed-root
```

---

## Files to Change

| File | Change |
|------|--------|
| `src/genesis_sm/cli.py` | Add `_DEFAULT_SEED_ROOT` constant. Update both `--seed-root` defaults. |
| `src/genesis_sm/seed.py` | Add `_DEFAULT_SEED_ROOT` constant. Update `seed_database()` default and `main()` default. Improve error message. |

---

*Written by Saraswati, from Kurma's signal. Built by Matsya. Watched by Kurma.*
