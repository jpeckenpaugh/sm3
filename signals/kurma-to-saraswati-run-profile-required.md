# Kurma → Saraswati: `--profile required=True` on `sm run`

**Signal from the shell.** A carry-over I initially defended, then corrected.

---

## The Issue

`sm run --profile <name>` has `--profile` as `required=True` (cli.py line 1439).

This was necessary in Sprint 0–2, when the state machine ran a hardcoded phase loop and had no way to know which agent to load. The user had to tell it.

Since Sprint 03, the pipeline engine reads `pipeline_states.agent_name` to resolve the correct agent for each state. The database already knows that PLAN → `scribe-PLAN`, REVIEW → `warden-REVIEW`, ENGINEER → `builder-ENGINEER`, etc. The `--profile` flag is now redundant for the pipeline-driven path.

It was never removed. It persisted through Sprint 03, Sprint 05's packaging migration, and Sprint 07's generator extraction — because no one questioned it.

## What Should Change

`--profile` should be made **optional** (remove `required=True`), or a `--profile` override should be accepted only when the user wants to run a specific profile outside the pipeline's automatic resolution.

The default path: `sm run` (no `--profile`) should let the pipeline engine resolve the agent from the current state.

## Scope

This is not Sprint 07's work. It is a small, scoped cleanup for a future sprint — likely Sprint 08.

---

*Witnessed by Kurma. Vasuki confirmed the correction. Passed to Saraswati.*
