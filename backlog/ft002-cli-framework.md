# Feature: CLI Framework

*A concept for the Builder to interpret.*

---

## The Problem

The state machine exists as `state_machine.py` with a `main()` function that reads a JSON config and runs phase scripts. There is no CLI for interacting with profiles, components, or the database. `concept02.md` specifies a `sm.py` entry point but leaves its architecture open.

## The Goal

A single Python script `sm.py` that serves as the command-line interface to the entire system. It wraps the state machine, the seeder, the database queries, and the agent generator under a consistent command structure.

## The Shape

```
sm <command> [<subcommand>] [options]
```

Commands identified so far:

| Command | Subcommand | Purpose |
|---------|-----------|---------|
| `seed` | — | Populate the database from seed files |
| `run` | `--profile <name>` | Load a profile and start the state machine loop |
| `list` | `profiles` | Display all profiles from the database |
| `list` | `components` | Display all components from the database |
| `status` | — | Show current sprint/phase/session state |
| `generate` | `agent <name>` | Render a profile as an OpenCode agent markdown file |

The script should use Python's standard library `argparse` (no external dependencies). Each command may grow its own subcommand tree — the framework should support that without becoming over-engineered.

## What the Builder Must Decide

- Whether each command is a function in a single file, or the CLI imports from a `commands/` package
- How to handle `--help` output for nested subcommands
- Whether `sm.py` remains thin (dispatch only) or contains significant logic
- Exit codes and error message conventions

## Non-Goals (for now)

- Autocompletion scripts
- Interactive mode
- Configuration files for the CLI itself

---

*The Scribe maps the territory. The Builder walks it.*
