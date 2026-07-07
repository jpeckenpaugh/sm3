# Feature: Variant Creation Workflow

*A concept for a future sprint. Not in scope for the next build.*

---

## The Problem

Creating a profile variant currently requires manually adding rows to `profiles` and `profile_components` — either via SQLite directly or by crafting seed JSON files. There is no user-facing command for saying *"make me a version of scribe that uses a different domain prompt."*

## The Shape

A set of `sm profile` subcommands:

```
sm profile create <name>                              # blank profile
sm profile clone <existing-name> --name <new-name>     # copy all components, then edit
sm profile edit <name> --add-component <type/name> --at <order>
sm profile edit <name> --remove-component <type/name>
sm profile edit <name> --set-param <type/name> <key>=<value>
```

The clone command is the most useful: it copies the source profile's `profile_components` rows (with order and params) to the new profile, then optionally applies overrides from flags.

### Example

```
sm profile clone scribe --name creative-scribe \
  --add-component prompt/scribe-domain-creative --at 2
```

This would:
1. Create new `profiles` row for `creative-scribe` (copy header/permissions from scribe)
2. Copy scribe's `profile_components` rows (obey-exactly, scribe-preamble, scribe-domain)
3. Insert the new component at position 2, shifting scribe-domain to position 3 (or replacing it)

## What This Requires First

- The component system must be working (ft001)
- The `sm list` commands must be working (ft004) so users can see available components
- Ideally, profile inheritance (ft007) so the clone references the parent instead of copying rows

## Open Questions

- Should clone deep-copy or use inheritance? Deep-copy is simpler; inheritance is more maintainable.
- Should there be interactive mode? ("Pick a base profile. Pick components to add/remove. Preview.")
- Does this overlap with `sm generate agent`? Generate is read-only output; this modifies the DB.

---

*Not yet scoped. Depends on base component system being operational first.*
