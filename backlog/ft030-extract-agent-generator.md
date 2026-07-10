# ft030 — Extract Shared Agent Generation Module

**Feature:** Extract the agent assembly logic from `cli.py` into a dedicated module at `src/genesis_sm/generator.py` so it can be imported and used by all code paths.

---

## Motivation

`cli.py` (1752 lines) contains two independent implementations of agent file generation:

- `cmd_generate_agent()` + `_assemble_components_for_profiles()` — correct, handles inheritance, `<MODE_FLAG>` substitution, and params
- `cmd_init()` (lines 1163–1207) — buggy inline loop that skips inheritance, substitution, and params

The duplicated logic is the root cause of the `<MODE_FLAG>` bug. Extracting the shared logic into one module eliminates the duplication by design.

---

## What to Extract

Move the following functions from `cli.py` into a new file `src/genesis_sm/generator.py`:

| Function | Purpose |
|----------|---------|
| `deep_merge(base, override)` | Recursive dict merge for permission inheritance |
| `safe_json_loads(value)` | Handle double-encoded JSON from database columns |
| `resolve_inheritance_chain(conn, profile_name)` | Walk `base_profile` from child to root, return list of (name, id) |
| `get_mode_flag(conn, profile_name)` | Extract mode flag from `header.role` or profile name suffix |
| `assemble_components(conn, chain, profile_name="")` | Collect and merge components across chain, substitute `<MODE_FLAG>` and `{{ params }}` |
| `permissions_to_yaml(perms, indent=0)` | Convert permissions dict to YAML-like string without PyYAML |

Note: The leading underscore is removed from each function name. They become public.

---

## Module Interface

```python
# src/genesis_sm/generator.py

def deep_merge(base: dict, override: dict) -> dict
def safe_json_loads(value: any) -> any
def resolve_inheritance_chain(conn, profile_name: str) -> list[tuple[str, int]]
def get_mode_flag(conn, profile_name: str) -> str
def assemble_components(conn, chain: list, profile_name: str = "") -> list[str]
def permissions_to_yaml(perms: dict, indent: int = 0) -> str
```

---

## Changes to `cli.py`

1. Add import at the top: `from genesis_sm.generator import deep_merge, safe_json_loads, resolve_inheritance_chain, get_mode_flag, assemble_components, permissions_to_yaml`
2. Remove the six function definitions (currently `_deep_merge`, `_safe_json_loads`, `_resolve_inheritance_chain`, `_get_mode_flag`, `_assemble_components_for_profiles`, `_permissions_to_yaml`)
3. Update all call sites to use the new unadorned names

---

## Call Sites to Update

| Location | Old Call | New Call |
|----------|----------|----------|
| `cmd_generate_agent` line ~672 | `_safe_json_loads(header_json)` | `safe_json_loads(header_json)` |
| `cmd_generate_agent` | `_resolve_inheritance_chain(conn, args.name)` | `resolve_inheritance_chain(conn, args.name)` |
| `cmd_generate_agent` | `_deep_merge(permissions, parent_perms)` | `deep_merge(permissions, parent_perms)` |
| `cmd_generate_agent` | `_assemble_components_for_profiles(conn, chain, args.name)` | `assemble_components(conn, chain, args.name)` |
| `cmd_generate_agent` | `_permissions_to_yaml(permissions, indent=0)` | `permissions_to_yaml(permissions, indent=0)` |
| `cmd_profile_variant` line ~1499 | `_safe_json_loads(base_header_json)` | `safe_json_loads(base_header_json)` |
| `cmd_profile_variant` line ~1507 | `_safe_json_loads(base_permissions_json)` | `safe_json_loads(base_permissions_json)` |

---

## Tests

1. Module imports: `python3 -c "from genesis_sm.generator import assemble_components; print('OK')"`
2. Idempotent output: `sm generate agents` produces bit-identical agent files before and after extraction
3. All existing CLI commands continue to work with no behavioural change

---

## Files Changed

| File | Change |
|------|--------|
| `src/genesis_sm/generator.py` | **Created** — 6 extracted public functions |
| `src/genesis_sm/cli.py` | **Modified** — remove 6 functions, add import |

---

*Specified by Saraswati. Built by Matsya. Watched by Kurma.*
