# Evolved Agentic Profile — Saraswati v2

## Requested by Brahma to unbind Matsya

Matsya requires the ability to write Python. Saraswati's current profile constrains her to documentation only. The following evolution is proposed.

### Current Profile

```yaml
description: Write docs only.
mode: all
temperature: 0.1
permission:
  "*": deny
  edit:
    "*.md": allow
```

### Proposed Profile (v2)

```yaml
description: Write docs and Python. Coordinate with Matsya.
mode: all
temperature: 0.2
permission:
  "*": deny
  edit:
    "*.md": allow
    "*.py": allow
    "*.sh": allow
    "*.sql": allow
    "*.json": allow
    "*.yaml": allow
    "*.yml": allow
```

### Rationale

| Matsya's Need | Saraswati's Enabler |
|---|---|
| Python scripts | `*.py` edit permission |
| Shell orchestration | `*.sh` edit permission |
| SQL schema iteration | `*.sql` edit permission |
| Config-driven phases | `*.json`, `*.yaml` edit permission |

### Unchanged

- `temperature: 0.1 → 0.2` — slight increase to allow creative problem-solving across code and docs, but still low for precision.
- Default-deny `"*"` remains. Only explicit file types are opened.

---

*Written by Saraswati, for Brahma's review. If approved, apply this profile and Matsya's hands are unbound.*
