# ft031 — Fix `cmd_init()` Agent Generation

**Feature:** Replace the duplicated inline agent generation block in `cmd_init()` with a call to the shared generator module extracted in ft030. This eliminates the root cause of the `<MODE_FLAG>` bug.

---

## The Bug

In `src/genesis_sm/cli.py`, function `cmd_init()` (lines 1163–1207), there is an inline loop that generates agent `.md` files during project bootstrap:

```python
for profile_name in agent_profiles:
    conn3 = sqlite3.connect(db_path)
    try:
        cursor = conn3.cursor()
        cursor.execute("SELECT name, version, header, permissions FROM profiles WHERE name = ?", (profile_name,))
        # ... reads columns, fetches direct profile_components only ...
        cursor.execute(
            """SELECT c.content FROM profile_components pc
               JOIN components c ON pc.component_id = c.id
               JOIN profiles p ON pc.profile_id = p.id
               WHERE p.name = ? ORDER BY pc.order_idx""",
            (profile_name,),
        )
        body_parts = [r[0] for r in cursor.fetchall() if r[0]]
        body = "\n\n".join(body_parts)
        # ... writes frontmatter + body to file ...
```

This code has three defects compared to the correct `cmd_generate_agent()` path:

1. **No inheritance resolution** — Only fetches components directly linked to the profile. Derived profiles (e.g. `scribe-PLAN`) miss inherited components from their base (`obey-exactly`, `scribe-preamble`, `scribe-domain`).
2. **No `<MODE_FLAG>` substitution** — The `bootstrap-protocol` component contains the literal string `<MODE_FLAG>` which is never replaced with the actual mode flag (e.g. `PLAN`, `ENGINEER`).
3. **No component params** — The `profile_components.params` column is not read or applied.

---

## The Fix

Replace the inline agent generation loop (lines 1163–1207) with a call to `cmd_generate_agents()` or to the shared `assemble_components()` function from `generator.py`.

The recommended approach: **iterate profiles and call `assemble_components()` directly**, since `cmd_init()` already has a loop over profiles and already reads profile data from the database.

### New Implementation

```python
# Inside cmd_init(), after seeding and schema setup:
from genesis_sm.generator import (
    assemble_components,
    resolve_inheritance_chain,
    permissions_to_yaml,
    safe_json_loads,
)

for profile_name in agent_profiles:
    conn3 = sqlite3.connect(db_path)
    try:
        cursor = conn3.cursor()
        cursor.execute(
            "SELECT name, version, header, permissions FROM profiles WHERE name = ?",
            (profile_name,),
        )
        row = cursor.fetchone()
        if not row:
            continue
        pname, pver, hdr_json, perm_json = row
        hdr = safe_json_loads(hdr_json)
        perms = safe_json_loads(perm_json)

        # Resolve inheritance
        chain = resolve_inheritance_chain(conn3, profile_name)

        # Merge permissions from entire chain (root to child)
        merged_perms = {}
        for chain_name, _ in chain:
            cursor.execute(
                "SELECT permissions FROM profiles WHERE name = ?", (chain_name,)
            )
            prow = cursor.fetchone()
            if prow and prow[0]:
                parent_perms = safe_json_loads(prow[0])
                if isinstance(parent_perms, dict):
                    deep_merge(merged_perms, parent_perms)

        # Assemble components using the shared generator
        body_parts = assemble_components(conn3, chain, profile_name)
        body = "\n\n".join(body_parts)

        description = hdr.get("role", profile_name)
        mode = hdr.get("mode", "all")
        temperature = hdr.get("temperature", 0.1)
        perm_yaml = permissions_to_yaml(merged_perms, indent=0)

        agent_md = f"""---
description: {description}
mode: {mode}
temperature: {temperature}
permission:
{perm_yaml}
---

{body}
"""
        output_path = os.path.join(agent_dir, f"{profile_name}.md")
        with open(output_path, "w") as f:
            f.write(agent_md)
    finally:
        conn3.close()
```

---

## What Is Removed

Delete the entire inline agent generation block, currently lines 1163–1207 in `cli.py`. This is approximately 45 lines of duplicated logic.

---

## Dependencies

This feature depends on **ft030** — the shared `generator.py` module must exist before this fix can be applied.

---

## Verification

After the fix, `cmd_init()` must produce identical output to `cmd_generate_agents()` for every profile:

```bash
# 1. Create a fresh project using init
rm -rf /tmp/test-init
sm init /tmp/test-init/matsya.db --yes

# 2. Generate agents via generate command
rm -rf /tmp/test-gen
mkdir -p /tmp/test-gen
cp /tmp/test-init/matsya.db /tmp/test-gen/matsya.db
cd /tmp/test-gen && sm generate agents --output-dir /tmp/test-gen/agents

# 3. Compare outputs
diff /tmp/test-init/.opencode/agents/ /tmp/test-gen/agents/
# Expected: no differences
```

Key checks:
- `scribe-PLAN.md` contains `PLAN`, not `<MODE_FLAG>`
- `scribe-PLAN.md` includes inherited components (`obey-exactly`, `scribe-preamble`, `scribe-domain`)
- `warden-GATE.md` contains `SPRINT_GATE`, not `<MODE_FLAG>`
- All derived profiles have the full inheritance chain assembled

---

## Files Changed

| File | Change |
|------|--------|
| `src/genesis_sm/cli.py` | **Modified** — replace lines 1163–1207 with correct generator calls |

---

*Specified by Saraswati. Built by Matsya. Watched by Kurma.*
