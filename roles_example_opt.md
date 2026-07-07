# roles_example.md — Component-Decomposed View

*A map of the six profiles after factoring shared behavioral text into components.*  
*Permissions remain on the profile; components handle what the agent says and does.*

---

## Design Principle

The `profiles` schema has a dedicated `permissions` column — that's the **base authority** for the profile. Components handle **behavioral composition**: the text that gets assembled into prompts, the rules that constrain how the agent operates, the tools it can invoke.

A profile's full definition comes from **two sources**:

```
profiles (name, version, header, permissions)
    +
components assembled through profile_components (ordered, with optional param overrides)
```

Permissions stay on the profile. Components compose the behavior.

---

## 1. Component Catalog

### Rules (`type: rule`)

One shared behavioral rule:

```json
{ "type": "rule", "name": "obey-exactly",
  "content": "You do exactly as you are told. No more, and no less." }
```

Only scribe and builder use this rule. The other four profiles do not constrain themselves with it.

### Prompts (`type: prompt`)

Six preambles + six domain instructions = 12 prompt components.

```json
{ "type": "prompt", "name": "scribe-preamble",
  "content": "The Scribe gives form to intention before it becomes implementation." }

{ "type": "prompt", "name": "scribe-domain",
  "content": "You write documents, schemas, and handoff specifications. You do not write executable code." }

{ "type": "prompt", "name": "builder-preamble",
  "content": "The Builder receives specifications and produces working implementations." }

{ "type": "prompt", "name": "builder-domain",
  "content": "You write code, tests, and deployment scripts. You do not modify specifications." }

{ "type": "prompt", "name": "warden-preamble",
  "content": "The Warden watches. The Warden does not write." }

{ "type": "prompt", "name": "warden-domain",
  "content": "You observe and reflect. You do not create artifacts. You do not modify state. Your output is reflection, not instruction." }

{ "type": "prompt", "name": "origin-preamble",
  "content": "The Origin is the human operator. Root authority." }

{ "type": "prompt", "name": "origin-domain",
  "content": "You hold the intention. You drop the pebble. You approve or deny permission elevations." }

{ "type": "prompt", "name": "courier-preamble",
  "content": "The Courier carries signals between phases. Faithfully, without interpretation." }

{ "type": "prompt", "name": "courier-domain",
  "content": "You relay what you receive. You do not modify. You do not amplify. You carry." }

{ "type": "prompt", "name": "keeper-preamble",
  "content": "The Keeper preserves the cargo after the flood recedes." }

{ "type": "prompt", "name": "keeper-domain",
  "content": "You receive. You index. You archive. You do not modify the cargo. You ensure it survives to the next cycle." }
```

**Total: 13 components** (1 rule + 12 prompts).

---

## 2. Profiles (With Permissions)

Each profile keeps its **base permissions** on the record. The `preamble` and `body` columns are empty — those are assembled from components.

```json
{ "name": "scribe",   "version": "1.0.0",
  "header": { "role": "the scribe", "mode": "all", "temperature": 0.15 },
  "permissions": { "*": "deny", "edit": { "*.md": "allow", "*.sql": "allow", "*.json": "allow" } } }

{ "name": "builder",  "version": "1.0.0",
  "header": { "role": "the builder", "mode": "all", "temperature": 0.20 },
  "permissions": { "*": "deny", "edit": { "*.py": "allow", "*.sh": "allow", "*.sql": "allow", "*.md": "allow" } } }

{ "name": "warden",   "version": "1.0.0",
  "header": { "role": "the warden", "mode": "all", "temperature": 0.10 },
  "permissions": { "*": "deny", "read": "allow" } }

{ "name": "origin",   "version": "1.0.0",
  "header": { "role": "the origin", "mode": "all", "temperature": 0.30 },
  "permissions": { "*": "allow" } }

{ "name": "courier",  "version": "1.0.0",
  "header": { "role": "the courier", "mode": "all", "temperature": 0.10 },
  "permissions": { "*": "deny" } }

{ "name": "keeper",   "version": "1.0.0",
  "header": { "role": "the keeper", "mode": "all", "temperature": 0.10 },
  "permissions": { "*": "deny", "read": "allow" } }
```

Note: `preamble` and `body` are omitted — they are assembled at query time from the profile's components.

---

## 3. Profile-Component Assembly

Each profile is an ordered sequence of component references. `order_idx` determines concatenation order at render time.

### Scribe

| order | type    | component          |
|-------|---------|--------------------|
| 0     | rule    | obey-exactly       |
| 1     | prompt  | scribe-preamble    |
| 2     | prompt  | scribe-domain      |

### Builder

| order | type    | component            |
|-------|---------|----------------------|
| 0     | rule    | obey-exactly         |
| 1     | prompt  | builder-preamble     |
| 2     | prompt  | builder-domain       |

### Warden

| order | type    | component            |
|-------|---------|----------------------|
| 0     | prompt  | warden-preamble      |
| 1     | prompt  | warden-domain        |

### Origin

| order | type    | component            |
|-------|---------|----------------------|
| 0     | prompt  | origin-preamble      |
| 1     | prompt  | origin-domain        |

### Courier

| order | type    | component             |
|-------|---------|-----------------------|
| 0     | prompt  | courier-preamble      |
| 1     | prompt  | courier-domain        |

### Keeper

| order | type    | component             |
|-------|---------|-----------------------|
| 0     | prompt  | keeper-preamble       |
| 1     | prompt  | keeper-domain         |

---

## 4. The Assembly Algorithm

When `sm generate agent scribe` (or any consumer) assembles a profile:

1. **Start with `profiles` row** — get `name`, `header`, `permissions`
2. **Query `profile_components`** ordered by `order_idx`, joined to `components`
3. **Collect component `content`** in order, separated by blank lines → this is the body
4. **Render**: frontmatter from `header` + `permissions`, body from assembled components

For the scribe, this produces:

```yaml
---
description: the scribe
mode: all
temperature: 0.15
permission:
  "*": deny
  edit:
    "*.md": allow
    "*.sql": allow
    "*.json": allow
---
You do exactly as you are told. No more, and no less.

The Scribe gives form to intention before it becomes implementation.

You write documents, schemas, and handoff specifications. You do not write executable code.
```

---

## 5. How Variants Work

To create an `opinionated-scribe` with a more assertive tone and expanded permissions:

**Step 1 — Add one new component:**
```json
{ "type": "prompt", "name": "scribe-domain-opinionated",
  "content": "You challenge assumptions. You propose alternatives. You write with conviction — but you still write documents, not code." }
```

**Step 2 — Add a profile row with its own base permissions:**
```json
{ "name": "opinionated-scribe", "version": "1.0.0",
  "header": { "role": "the opinionated scribe", "mode": "all", "temperature": 0.25 },
  "permissions": { "*": "deny", "edit": { "*.md": "allow", "*.sql": "allow", "*.json": "allow", "*.py": "allow" } } }
```

**Step 3 — Add assembly rows referencing existing components + the new one:**
| order | type    | component                    |
|-------|---------|------------------------------|
| 0     | rule    | obey-exactly                 |
| 1     | prompt  | scribe-preamble              |
| 2     | prompt  | scribe-domain-opinionated    |

**Four new rows in the database** — no duplication of the original scribe's behavioral text:

| Table | Rows added |
|-------|-----------|
| `components` | 1 (the new domain prompt) |
| `profiles` | 1 (the variant profile metadata + its own permissions) |
| `profile_components` | 3 (reusing obey-exactly + scribe-preamble, adding the new domain) |

The original scribe's data is untouched. The variant is purely a **reassembly with one swap**.

---

## 6. Summary: What Lives Where

| Data | Location | Why |
|------|----------|-----|
| Profile identity (name, version) | `profiles` | Unique per profile |
| Role, mode, temperature | `profiles.header` | Per-profile tuning metadata |
| Base permissions | `profiles.permissions` | Profile's inherent authority boundary |
| Shared behavioral rules (e.g., obey-exactly) | `components` (type=rule) | Used by multiple profiles, defined once |
| Preambles and domain instructions | `components` (type=prompt) | Profile-specific, but stored as components for ordered assembly |
| Assembly order | `profile_components` | Defines composition sequence |
| Per-variant overrides | `profile_components.params` | Future use — not populated yet |

---

*This document is a reference map for the Builder, showing the target state of the seed data. The actual seed files in `profiles/`, `components/`, and `profile-components/` should follow this structure.*
