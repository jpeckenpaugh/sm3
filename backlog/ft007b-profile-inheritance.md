# Feature: Profile Inheritance (Parent Pointer)

*A concept for a future sprint. Not in scope for the next build.*

---

## The Problem

Creating a variant of an existing profile (e.g., `creative-scribe` from `scribe`) requires manually replicating the shared `profile_components` rows. The common components (`obey-exactly`, `scribe-preamble`) must be re-listed for each variant even though they don't change. At small scale this is manageable; at 20+ profiles it becomes repetitive and error-prone.

The schema has no mechanism for saying *"this profile is like that one, except..."*

## The Shape

A new optional column on `profiles`:

```sql
ALTER TABLE profiles ADD COLUMN extends INTEGER REFERENCES profiles(id);
```

Where `extends = NULL` means "root profile" (the six canonical roles), and `extends = <parent_id>` means "inherit all of my parent's `profile_components`, then overlay my own."

The assembly algorithm becomes:

1. Walk the `extends` chain from child up to root
2. Collect `profile_components` at each level
3. Merge: child entries override parent entries on matching `component_id`
4. Resolve `params` cumulatively (child params merge onto parent params)

### Example

```
scribe (extends = NULL)
  ├── creative-scribe (extends = scribe)
  │     └── profile_components: [ scribe-domain-creative (order 2, replaces scribe-domain) ]
  └── conservative-scribe (extends = scribe)
        └── profile_components: [ obey-exactly (order 0, params: { "tone": "strict" }) ]
```

`creative-scribe` inherits `obey-exactly` + `scribe-preamble` from scribe, then overrides `scribe-domain` with its own. `conservative-scribe` inherits everything but adds a param override to the obedience rule.

## What This Enables

- Profile taxonomies: a tree of roles instead of a flat list
- Sparse definitions: variants only store what they change
- Mass updates: change a shared component and all derived profiles pick it up

## Open Questions

- Should `extends` support multiple inheritance? (Probably not — tree, not DAG.)
- What happens if a parent profile is deleted? Cascade? Nullify? Block?
- How does `sm list profiles` display inheritance chains?

---

*Not yet scoped. The schema is forward-compatible with this addition.*
