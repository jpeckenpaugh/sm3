# Schema

## Overview

Three tables to model agent profiles and their composable parts. JSON columns for flexibility. Recursion acknowledged but deferred.

## Tables

### profiles

| Column      | Type     | Notes                              |
|-------------|----------|------------------------------------|
| id          | INTEGER  | PRIMARY KEY AUTOINCREMENT          |
| name        | TEXT     | UNIQUE, NOT NULL                   |
| version     | TEXT     | semver                             |
| header      | TEXT     | JSON — LLM system prompt fragment  |
| permissions | TEXT     | JSON — tool scopes                 |
| preamble    | TEXT     | markdown preamble                  |
| body        | TEXT     | markdown body                      |
| created_at  | TEXT     | ISO 8601                           |
| updated_at  | TEXT     | ISO 8601                           |

### components

| Column      | Type     | Notes                              |
|-------------|----------|------------------------------------|
| id          | INTEGER  | PRIMARY KEY AUTOINCREMENT          |
| type        | TEXT     | e.g. "tool", "prompt", "rule"      |
| name        | TEXT     | UNIQUE within type                 |
| content     | TEXT     | JSON or markdown                   |
| created_at  | TEXT     | ISO 8601                           |

### profile_components

| Column       | Type     | Notes                              |
|--------------|----------|------------------------------------|
| id           | INTEGER  | PRIMARY KEY AUTOINCREMENT          |
| profile_id   | INTEGER  | FK → profiles(id)                  |
| component_id | INTEGER  | FK → components(id)                |
| order_idx    | INTEGER  | rendering order                    |
| params       | TEXT     | JSON — per-instance overrides      |

## Rationale

- **JSON columns** (`header`, `permissions`, `params`) allow forward-compatible changes without migrations.
- **profile_components** junction table enables many-to-many composition and ordering.
- **No hard FK constraints on JSON columns** — parsed at read time, not write time.

## Open Questions (for Matsya)

1. Should `components.content` be a separate table with versioning?
2. How does `is_meta` from sprints relate to profiles — same concept or different?
3. Should profile inheritance (extends) be stored inline or as a separate link table?
