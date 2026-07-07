# Feature: Profile Export / Import

*A concept for a future sprint. Not in scope for the next build.*

---

## The Problem

Profiles currently exist only inside the SQLite database. There is no portable way to share a profile (including its components and assembly) between instances, back it up as a single artifact, or version it independently.

## The Shape

```
sm export profile <name> [--format json] [--output <file>]
sm import profile <file> [--name <override>]
```

### Export format

A self-contained JSON bundle that includes everything needed to recreate the profile:

```json
{
  "profile": { "name": "scribe", "version": "1.0.0", "header": { ... }, "permissions": { ... } },
  "components": [
    { "type": "rule", "name": "obey-exactly", "content": "..." },
    { "type": "prompt", "name": "scribe-preamble", "content": "..." },
    { "type": "prompt", "name": "scribe-domain", "content": "..." }
  ],
  "profile_components": [
    { "component_ref": "rule/obey-exactly", "order_idx": 0, "params": {} },
    { "component_ref": "prompt/scribe-preamble", "order_idx": 1, "params": {} },
    { "component_ref": "prompt/scribe-domain", "order_idx": 2, "params": {} }
  ]
}
```

### Import behavior

- Upserts the profile
- Upserts components (match on `(type, name)`, update if newer or different)
- Rebuilds `profile_components` rows
- Optional `--name <override>` to import under a different profile name (for creating variants)

## What This Enables

- Profile sharing between projects
- Version-controlling profiles as JSON files in git (alongside the DB)
- Bootstrapping a new instance from an exported profile library

## Open Questions

- Should import overwrite existing profiles or refuse? (--force flag?)
- How to handle component conflicts — same `(type, name)` but different `content`?
- Should export resolve inheritance chains (ft007) into self-contained flat bundles?

---

*Not yet scoped. Requires the base component system to be stable first.*
