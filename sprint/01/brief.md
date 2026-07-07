# Sprint 01 — Brief for the Engineer

*Additional context and design decisions not captured in the feature concepts.*

---

## The Goal

Turn the flat, hand-written profiles in `roles_example.md` into a **database-backed, component-driven system** where:

- `profiles` stores identity + permissions
- `components` stores reusable behavioral text (preambles, domain instructions, shared rules)
- `profile_components` defines ordered assembly
- `sm.py` provides CLI access to seed, query, run, and generate
- `.opencode/agents/*.md` become generated artifacts, not manual inputs

---

## Key Design Decisions (made by Scribe + Warden)

### Permissions live on the profile, not in components

The `profiles` table has a dedicated `permissions` column with a JSON default. This is the **base authority** for each role. Components handle *what the agent says and does* (behavioral text), not *what it's allowed to access*.

| What | Where |
|------|-------|
| Base permissions | `profiles.permissions` |
| Shared behavioral rules | `components` (type=rule) |
| Preambles and domain text | `components` (type=prompt) |
| Assembly order | `profile_components` (order_idx) |
| Per-variant overrides | `profile_components.params` (not used in this sprint) |

### Only one shared rule component: `obey-exactly`

"You do exactly as you are told. No more, and no less." appears in scribe and builder bodies. It is the only text fragment shared across multiple profiles. It becomes a single `rule` component referenced by both.

The other four profiles (warden, origin, courier, keeper) do **not** use this rule.

### `preamble` and `body` columns are optional

These columns exist in the schema but their content is now assembled from components. The seed may leave them empty, omit them, or populate them as a cached convenience — the Builder decides.

### `description` in agent file frontmatter

The `description:` field in the generated OpenCode agent file can come from `header.role`, from the preamble component, or from a dedicated field — the Builder decides. See ft006 for discussion.

### Order of assembly matters

`profile_components.order_idx` determines the sequence. The convention is:

| order | content |
|-------|---------|
| 0 | Shared rules (e.g., obey-exactly) |
| 1 | Preamble |
| 2 | Domain instructions |

This produces a body text that reads naturally: *"You do exactly as you are told... The Scribe gives form... You write documents..."*

---

## File Layout Target

After seeding, the seed data directory should look like:

```
profiles/
  scribe.json          → name, version, header, permissions
  builder.json
  warden.json
  origin.json
  courier.json
  keeper.json

components/
  rules/
    obey-exactly.json
  prompts/
    scribe-preamble.json
    scribe-domain.json
    builder-preamble.json
    builder-domain.json
    warden-preamble.json
    warden-domain.json
    origin-preamble.json
    origin-domain.json
    courier-preamble.json
    courier-domain.json
    keeper-preamble.json
    keeper-domain.json

profile-components/
  scribe.json
  builder.json
  warden.json
  origin.json
  courier.json
  keeper.json
```

See `roles_example_opt.md` for the full content of each file.

---

## Existing Code That Must Not Break

- `state_machine.py` must remain importable as a module (already mostly there — `main()` is a function)
- The existing `config.json` format should still work
- Phase scripts in `scripts/` should not change
- The existing `.opencode/agents/` files should remain until `sm generate agent` overwrites them

---

## The Variant Test

Before closing this sprint, the system should be able to produce an `opinionated-scribe` by:

1. Adding one new component (`scribe-domain-opinionated`)
2. Adding one new profile row (with its own permissions)
3. Adding three `profile_components` rows (reusing `obey-exactly` and `scribe-preamble`)

No duplication of existing data. This is the litmus test that the decomposition is correct.

---

## Files the Engineer Should Read First

| File | Why |
|------|-----|
| `schema.sql` | The database schema — ground truth |
| `roles_example.md` | Original flat profile data |
| `roles_example_opt.md` | Component-decomposed reference map |
| `concept02.md` | Original specification this sprint implements |
| `state_machine.py` | Existing state machine — will be imported as a module |
| `backlog/ft001.md` through `ft006.md` | Feature concepts for this sprint |
| `.opencode/agents/the-scribe.md` | Example of the output format for ft006 |

---

*Written by the Scribe. Built by the Engineer. Watched by the Warden.*
