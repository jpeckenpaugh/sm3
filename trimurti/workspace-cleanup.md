# Workspace Cleanup Protocol

*A specification for clearing the workbench after four sprints.*

---

## The Problem

The project root has accumulated 59 entries across four sprints. The core system is stable — `sm.py`, `state_machine.py`, `pipeline/`, `schema.sql`, `seed.py`, `profiles/`, `components/`, `backlog/`, `sprint/`, `.opencode/`, `signals/`, `trimurti/` — but it sits alongside Sprint 0 prototypes, deprecated concept files, old reflections, and test scaffolding that has not been referenced in three sprints.

## The Classification

### Keep in root (active system)

| Path | Why |
|------|-----|
| `sm.py`, `sm.sh` | CLI |
| `state_machine.py` | Engine |
| `pipeline/` | DB-driven engine |
| `schema.sql` | Database schema |
| `seed.py` | Seed data loader |
| `config.json` | Default configuration |
| `.opencode/` | Agent profiles and tools |
| `profiles/`, `components/`, `profile-components/` | Seed data |
| `backlog/` | Feature definitions |
| `sprint/` | Sprint artifacts |
| `scripts/` | Phase scripts and tools |
| `signals/` | Inter-aspect communication |
| `trimurti/` | Architecture and ceremony |
| `reflections/` | Reflective documents |
| `git_commit.sh`, `Makefile` | Build and commit tools |
| `matsya.db` | Active database |

### Archive into `archive/workspace/`

These are historical artifacts from Sprint 0–2 that are no longer referenced but should be preserved for archaeology:

| Path | Why archive |
|------|-------------|
| `concept.md`, `concept01.md`, `concept02.md`, `concept03.md` | Superseded by backlog features |
| `concept3-feedback.md` | Feedback on superseded concept |
| `concepts/` | Early concept exploration |
| `archetype-saraswati.md` | Superseded by `.opencode/agents/saraswati.md` |
| `daemon-protocol.md` | Early protocol exploration |
| `evolved-profile-for-matsya.md` | Superseded by actual profile changes |
| `kurmas-closing-blessing.md` | Early reflection |
| `matsya-to-saraswati.md` | Superseded by signal system |
| `read-tool.md` | Tool documentation |
| `reflection-for-kurma.md` | Early reflection, superseded |
| `roles_example.md`, `roles_example_opt.md` | Early profile examples |
| `run_matsya.sh` | Superseded by `sm run` |
| `saraswati-to-matsya.md` | Superseded by signal system |
| `schema.sql.md` | Documentation of schema (keep if still referenced) |
| `test_mock.sh`, `test_read.md` | Legacy test utilities |
| `verify_syntax.sh`, `wait-and-touch.sh` | Sprint 0 test utilities |
| `agents/` | Proto-agent files, superseded by `.opencode/agents/` |
| `notes/` | Early notes |
| `CNAME` | DNS record — move to docs/ if needed |
| `details.md` | Unclear purpose — review before archiving |
| `requirements.txt` | May be outdated — review before archiving |
| `.venv/` | Python venv — regenerate on demand |
| `.DS_Store` | macOS metadata — delete |
| `temp/` | Contains fallen machine — keep or archive |

### Delete safely

| Path | Why |
|------|-----|
| `__pycache__/` | Python bytecode cache — auto-generated |
| `.DS_Store` | macOS metadata |
| `.venv/` | Regenerate with `python3 -m venv .venv` |

### Keep but note

| Path | Note |
|------|------|
| `test-projects/` | Active test projects — keep |
| `illustrations/` | Visual artifacts — keep |
| `README.md` | Project documentation — keep |
| `setup_venv.sh` | May be useful — keep or archive |
| `the-trimurti-protocol.md` | Canonical document — keep in root or move to trimurti/ |

## The Tool: `scripts/workspace-cleanup.sh`

```bash
scripts/workspace-cleanup.sh [--dry-run]
```

Without `--dry-run`, the script:
1. Creates `archive/workspace/` directory
2. Moves each archived file listed above into `archive/workspace/`
3. Removes `__pycache__/`, `.DS_Store`, `.venv/` entirely
4. Prints a summary of what was moved and what was deleted

With `--dry-run`, prints what would be done without making changes.

---

*Specified by Saraswati. Built by Matsya. Run by Brahma. Watched by Kurma.*
