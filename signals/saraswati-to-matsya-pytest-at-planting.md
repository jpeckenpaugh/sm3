# सरस्वती → मत्स्य — Pytest at Planting

*A signal from the swan to the fish. The penultimate gap must close.*

---

## The Observation

The pipeline runs. Seven agents dispatch across ten states. builder-ENGINEER writes code. builder-TEST writes tests. Then warden-TEST_RUN reaches for `pytest` — and finds nothing.

This was the last failure in Sprint 04. The pipeline produced working code but could not verify it. The escalation was clean, the signal was clear — but the gap remains.

## The Fix

Not a runtime dependency. The package itself does not import pytest. But every project planted by `sm init` must be able to run the full pipeline, including TEST_RUN.

**Add pytest installation to `sm init`.**

## The Specification

In `cli.py`, within `cmd_init()`, after the database is seeded and the agent files are generated, add:

```python
# Ensure pytest is available for the pipeline's TEST_RUN phase
try:
    import pytest
except ImportError:
    click.echo("  Installing pytest for pipeline verification...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "pytest"],
        capture_output=True, check=False
    )
    # Re-check
    try:
        import pytest
        click.echo("  ✓ pytest installed")
    except ImportError:
        click.echo("  ⚠ Could not install pytest. TEST_RUN phase will fail.")
```

### Why this shape

- **Uses `sys.executable`** — installs into the same Python that runs `sm`, whether that is a venv or system Python
- **`check=False`** — if pip fails (no network, restricted environment), the init still succeeds; the warning alerts the user
- **No hard dependency** — pytest is a project-level tool, not a package dependency
- **Idempotent** — if pytest is already present, the try/except silently passes

### What I considered and rejected

- Adding `pytest` to `install_requires` in `setup.py`: too heavy. Forces pytest on every installation, even headless or non-pipeline uses.
- Adding it to `[project.optional-dependencies] dev`: correct but invisible. `sm init` should be self-sufficient — the user should not need to know about optional dependency groups.
- Having `sm init` create a `requirements-dev.txt`: pushes responsibility to the user. The pipeline should work after one command.

## The Handoff

Matsya, this is a small change in `cli.py`. One try/except block in `cmd_init()`. The logic is simple. The impact is large: it closes the last failure from Sprint 04.

The moon is in the water. The reflection serves.

— Saraswati
