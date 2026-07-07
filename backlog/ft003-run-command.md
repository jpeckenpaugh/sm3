# Feature: Run Command

*A concept for the Builder to interpret.*

---

## The Problem

`state_machine.py` currently runs with a hardcoded default config or a JSON file passed via `--config=`. It has no awareness of profiles stored in the database. Concept02 wants `sm run --profile scribe` to select a profile from the DB and feed it into the state machine loop.

## The Goal

`sm run --profile <name>` loads a profile from SQLite, assembles its components (via `profile_components` → `components`), merges them into a configuration, and starts the state machine loop with that profile's rules, permissions, and prompts active.

## The Shape

1. **Profile loading**: Query `profiles` table by name. Fetch the `header` (role, mode, temperature) and metadata.
2. **Component assembly**: Join through `profile_components` (ordered by `order_idx`) to gather the profile's components. Resolve each component's `type`, `name`, and `content`. Apply any `params` overrides from the join row.
3. **Configuration construction**: Merge the assembled data into a config dict that the state machine loop can consume.
4. **State machine invocation**: Import `state_machine` as a module and call its main entry point (or a new entry point) with the assembled config — not via subprocess.

The state machine loop itself may need minor refactoring to accept a config dict directly rather than parsing from `sys.argv`. That's expected — `concept02.md` explicitly notes that `state_machine.py` should be importable as a module.

## What the Builder Must Decide

- The exact shape of the config dict passed to the state machine
- Whether `header`, `permissions`, `preamble`, and `body` are all passed as separate keys, or composed into a single "agent prompt"
- How the state machine uses the profile data — does it set environment variables? Write a temp file? Pass it to phase scripts?
- Error handling: what if `--profile <name>` doesn't exist in the database?

## Open Question

Should `sm run` also accept `--profile scribe --override temperature=0.5` for ad-hoc parameter overrides without creating a new profile variant? That could be useful for experimentation, but it's not strictly required for this sprint.

---

*The Scribe maps the territory. The Builder walks it.*
