# Feature: Component Params Override System

*A concept for a future sprint. Not in scope for the next build.*

---

## The Problem

The `profile_components.params` column exists as a JSON blob for "overrides," but there is no defined system for how params interact with component content at assembly time. Currently all params are empty `{}`. A variant that needs a stricter tone or a different temperature has no defined mechanism to express that.

## The Shape

A convention for how `params` modifies component `content` at assembly time:

### Variable substitution (template strings)

```json
// components/rule/obey-exactly.json
{ "content": "{{ rule }} You do exactly as you are told. No more, and no less." }

// profile_components params for conservative-scribe
{ "params": { "rule": "[STRICT]" } }

// Assembled output:
// "[STRICT] You do exactly as you are told. No more, and no less."
```

### Permission merging

```json
// profile_components params for creative-scribe
{ "params": { "permissions": { "edit": { "*.py": "allow" } } } }

// Assembled: creative-scribe's base permissions (from profiles.permissions)
// are merged with this override → "*.py" is added to the edit allowlist
```

### Value overrides for header fields

```json
// profile_components params
{ "params": { "temperature": 0.3 } }

// Assembled: the profile's header.temperature is overridden to 0.3
// This allows a variant to keep the same profile metadata but tune behavior
```

## What This Enables

- Template-driven components: one component can produce different outputs per profile
- Non-destructive overrides: base profile stays clean, variants layer on top
- The `params` column finally fulfills its design purpose

## Open Questions

- Template syntax — `{{ var }}` like Jinja? `{var}` like Python format strings? A custom syntax?
- Deep merge vs shallow merge for nested JSON (permissions in particular)
- Should params be validated against a schema per component type?

---

*Not yet scoped. Requires the base assembly pipeline to be working first.*
