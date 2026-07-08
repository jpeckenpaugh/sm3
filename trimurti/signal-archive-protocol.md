# Signal Archive Protocol

*A convention for how signals between the Trimurti aspects are preserved, not destroyed.*

---

## The Problem

Signals are the shared membrane between Saraswati, Matsya, and Kurma during a sprint. They carry questions, proposals, reflections, and decisions. When a signal is deleted before all three aspects have read it, the *temperature* of the discussion is lost — the reasoning behind decisions is erased even if the decisions themselves persist in artifacts.

During Sprint 04, `git add -A` in `git_commit.sh` swept away signals that Kurma had not yet read. The decisions survived in seed data and code, but Kurma saw only the outcome, not the churn that produced it.

## The Shape

Signals are never deleted. They are **archived** under `signals/archive/YYYY-MM-DD/` after all three aspects have acknowledged them.

### Directory structure

```
signals/
  archive/
    2026-07-08/
      kurma-to-matsya-the-fundamentals.md
      matsya-to-saraswati-silt-and-path.md
      saraswati-to-matsya-the-expanded-pantheon.md
      ...
  kurma-closing-sprint-4.md              ← current, not yet archived
  saraswati-to-matsya-tools-and-proxy.md  ← current, not yet delivered
```

### The tool: `scripts/archive-signals.sh`

A shell script that moves all signals from `signals/` into a dated archive subdirectory.

```bash
scripts/archive-signals.sh [--date YYYY-MM-DD]
```

Default date is today. The script:

1. Creates `signals/archive/YYYY-MM-DD/` if it does not exist
2. Moves every `.md` file from `signals/` into `signals/archive/YYYY-MM-DD/`
3. Does NOT touch files already in `signals/archive/`
4. Reports count of archived files

### When to run it

At the end of a sprint, after all three aspects have acknowledged the closing signal.
Specifically:

1. Kurma writes the closing reflection
2. Saraswati reads it and acknowledges
3. Matsya reads it and acknowledges
4. **Brahma runs `bash scripts/archive-signals.sh`**
5. The sprint's signals are preserved under a dated directory
6. The `trimurti/` directory holds the durable specifications and reflections

### What should NOT be archived into signals

- `trimurti/` — permanent specifications, tool designs, architecture documents
- `backlog/` — feature definitions
- `profiles/`, `components/`, `pipeline/` — seed data and code
- `signals/archive/` — already preserved

Signals are for ephemeral conversation between the three aspects during a sprint.
Everything else has a permanent home elsewhere.

### Integration with git_commit.sh

The `git_commit.sh` script should **not** run `git add -A`. Instead, it should stage specific paths:

```bash
git add pipeline/ profiles/ components/ schema.sql seed.py sm.py state_machine.py backlog/ft016-*.md
git add sprint/03/ trimurti/ .opencode/agents/
# Do NOT add signals/ — they are archived separately
```

This prevents accidental deletion of unread signals.

---

*Specified by Saraswati. Built by Matsya. Run by Brahma. Watched by Kurma.*
