# Feature: Seed & Component Decomposition

*A concept for the Builder to interpret.*

---

## The Problem

`concept02.md` describes six flat profile JSON files that mirror the `profiles` table schema. But the schema also contains `components` and `profile_components` tables — designed for reusable, composable building blocks. The flat approach duplicates text (e.g., "You do exactly as you are told. No more, and no less." appears in both scribe and builder), making variants harder to create and maintenance more error-prone.

## The Goal

The `sm seed` command should populate **all three tables** — `profiles`, `components`, and `profile_components` — from seed data. The flat `body` field in `profiles` is no longer the canonical source of a profile's behavior; instead, the ordered assembly of components via `profile_components` becomes the truth.

Permissions are the exception: they remain on the `profiles` table as a first-class attribute. Each profile carries its own base authority. Components handle behavioral text only (preambles, domain instructions, shared rules like `obey-exactly`).

## The Shape

A new seed data layout:

```
profiles/
  scribe.json          # name, version, header, permissions
  builder.json
  warden.json
  origin.json
  courier.json
  keeper.json

components/
  rules/
    obey-exactly.json      # only shared behavioral rule
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
  scribe.json           # ordered list of component references (no permissions here)
  builder.json
  warden.json
  origin.json
  courier.json
  keeper.json
```

Note: Permissions are **not** components. They live in `profiles/*.json` alongside `header` and `version`. The `components/rules/` directory contains only behavioral rules like `obey-exactly`. See `roles_example_opt.md` for the full reference map.

The `seed.py` script reads these directories and upserts into the corresponding tables. Idempotent. Order-preserving.

## What the Builder Must Decide

- The exact JSON schema for each seed file (keys, nesting, required vs optional fields)
- How `profile-components/` references components — by `(type, name)` pair or by some other identifier
- Whether `preamble` and `body` fields in `profiles/*.json` are omitted entirely, left empty, or populated as a cached assembly
- Error handling: what happens when a component reference in `profile-components/` has no matching entry in `components/`

## Open Questions

1. Should `components/` and `profile-components/` be seeded from individual files (many small files) or from a single aggregated seed file per directory? The file-per-component approach is more modular; the aggregated approach is easier to review. Either is valid — the Builder chooses.

2. The `profile_components` table has a `params` column (JSON overrides). Should the base seed populate it (e.g., for temperature overrides on shared components), or leave it empty for future use? Currently deferred — empty is fine.

---

*The Scribe maps the territory. The Builder walks it.*
