# Feature: Profile Cleanup — Merge Base + Derived Permissions

*A fix for the universal tools bug. The generator must walk the inheritance chain for permissions, same as it does for components.*

---

## The Problem

`cmd_generate_agent()` in `cli.py` (line 582) loads permissions only from the derived profile:

```python
permissions = json.loads(permissions_json)  # derived profile only
```

The three universal tools (`search_files`, `list_files`, `file_tree`) are declared in base profiles (`scribe.json`, `builder.json`, `warden.json`) but never appear in generated agent files because the generator does not merge base + derived permissions.

**Consequence:** Generated agent files for scribe-PLAN, builder-ENGINEER, warden-TEST_RUN, etc. are missing the universal tools. At runtime, these agents may not be able to search, list files, or see the project tree.

## The Fix

In `cmd_generate_agent()`, after resolving the inheritance chain (which it already does for components), merge permissions from all profiles in the chain — root first, child last, child overrides parent.

### Current code (line 582)
```python
permissions = json.loads(permissions_json)
```

### New code
```python
# Merge permissions from entire inheritance chain
permissions = {}
for profile_name, _ in chain:  # chain is root-to-child
    cursor.execute(
        "SELECT permissions FROM profiles WHERE name = ?",
        (profile_name,),
    )
    row = cursor.fetchone()
    if row and row[0]:
        parent_perms = json.loads(row[0])
        # Deep merge: child keys override parent keys
        _deep_merge(permissions, parent_perms)
```

Where `_deep_merge` recursively merges dicts, with child values overriding parent:

```python
def _deep_merge(base, override):
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
```

This is the same pattern used by `_assemble_components_for_profiles()` for component content — now applied to permissions too.

### Backward compatibility

- Profiles without a base_profile (standalone like `origin.json`) have a chain of length 1 — their own permissions only, unchanged behavior.
- Profiles with a base_profile now get merged permissions. The derived profile's explicit permissions override the base's, but base-level tools not overridden are inherited.
- No schema change. No seed data change. No new columns.

### Verification

Generate each derived agent file and confirm the generated frontmatter includes:

```
permission:
  "*": deny
  read: allow
  edit: ...
  websearch: allow
  webfetch: deny
  search_files: allow     # <-- inherited from base
  list_files: allow       # <-- inherited from base
  file_tree: allow        # <-- inherited from base
  read_pulse: allow       # <-- from derived profile
```

---

*Specified by Saraswati. Built by Matsya. Witnessed by Kurma.*
