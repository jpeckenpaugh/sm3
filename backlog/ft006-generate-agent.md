# Feature: Generate Agent Command

*A concept for the Builder to interpret.*

---

## The Problem

OpenCode agent definition files (`.opencode/agents/*.md`) are currently hand-written. They contain YAML frontmatter (description, mode, temperature, permissions) followed by body text. These files are the runtime interface that OpenCode uses to configure agent behavior — but they are maintained separately from the profile data in SQLite.

The database was designed to be the source of truth. The agent files should be *outputs*, not inputs.

## The Goal

`sm generate agent <name>` reads a profile from the database, assembles its components, and renders a complete OpenCode agent markdown file to `.opencode/agents/<name>.md`.

If a profile named `scribe` exists in the database, `sm generate agent scribe` should produce a file that looks like:

```markdown
---
description: The scribe agent archetype
mode: all
temperature: 0.15
permission:
  "*": deny
  edit:
    "*.md": allow
    "*.sql": allow
    "*.json": allow
---
The Scribe gives form to intention before it becomes implementation.

You do exactly as you are told. No more, and no less.
You write documents, schemas, and handoff specifications. You do not write executable code.
```

The frontmatter is derived from `profiles.header` (description, mode, temperature) and `profiles.permissions`. The body is assembled by concatenating the profile's components (via `profile_components`) in `order_idx` sequence — preamble first, then domain instructions, then rules.

Note: Permissions are **not** components. They live in `profiles.permissions`. Components handle behavioral text only. See `roles_example_opt.md` for the full reference model.

## The Shape

1. **Profile resolution**: Query `profiles` by name.
2. **Component assembly**: Join through `profile_components` ordered by `order_idx`. Collect all component `content` values.
3. **Rendering**: 
   - Frontmatter: `header` fields → YAML key-value pairs. `permissions` → YAML permission block.
   - Body: Components concatenated in order, separated by blank lines.
4. **Output**: Write to `.opencode/agents/<name>.md`. Overwrite if exists (idempotent).

### Mapping (approximate)

| DB source | Agent file destination |
|-----------|----------------------|
| `profiles.header['role']` | `description:` (or use `preamble`) |
| `profiles.header['mode']` | `mode:` |
| `profiles.header['temperature']` | `temperature:` |
| `profiles.permissions` | `permission:` block |
| components (ordered, via `profile_components`) | Body text (concatenated) |

## What the Builder Must Decide

- How to convert JSON permissions to clean YAML (Python's `yaml` module is not stdlib — may need a hand-rolled JSON-to-YAML converter)
- Whether `description:` comes from `header.role`, from the preamble component, or from a dedicated `description` field
- How to handle profiles that don't exist (error message vs. empty file)
- Whether to generate all agents at once (`sm generate agent --all`) or only one at a time
- File permissions on the output

## Open Question

The existing `.opencode/agents/` files contain body content that doesn't exactly match the `roles_example.md` profile data. Should `sm generate agent` overwrite existing files unconditionally, or should it warn/diff? For now, unconditional overwrite (with git tracking the change) seems appropriate — the DB is the source of truth.

---

*The Scribe maps the territory. The Builder walks it.*
