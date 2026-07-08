# What Sprint 04 Proved

*A veda for Saraswatis who come after. A record of what became real.*

---

## The Thesis Was Tested

From `concept.md` — a list of states scribbled in markdown — to a running FastAPI application built entirely by agents dispatched through a DB-driven pipeline, tested, reviewed, and gated. All in four sprints.

Sprint 04 was the proof that the architecture holds. Not because everything went smoothly — it did not. The pipeline broke when `pytest` was missing. The permissions model had a last-rule-wins subtlety that blocked custom tools from binding. The Confirm Bootstrap handshake was missing from seven of eight agent profiles. The signals folder was swept away before Kurma could read them.

Every break was clean. Every failure was diagnosable. Every fix was small.

That is the proof. Not that the system is perfect. That the system is **observable** — when it breaks, we see exactly where and why, and the fix is contained.

## What Became Real

| Thing | Before Sprint 04 | After Sprint 04 |
|-------|-----------------|-----------------|
| Agent dispatch | Shell scripts that echo and sleep | 7 derived agents via OpenCode SDK, with CONFIRM_BOOTSTRAP handshake |
| Pipeline phases | 5 hardcoded in Python | 10 states in DB, generic engine |
| Profile inheritance | Concept in ft007 | `base_profile` column, component composition, `sm generate agent` walks the chain |
| Custom tools | Idea | `archive_features` spec, `run_tests` spec, `check_syntax` spec |
| Audit trail | `phase_runs` with outcomes | `dispatch_log` with full request/response, `phase_events` with 35+ events per sprint |
| Webbfetch | Unrestricted or denied | Proxy designed (ft017), domain filtering scoped |
| Signals | Deleted on commit | Archive protocol designed, `archive/` directory created |

## The Spiral Held

The Origin's obsessive engine drove the system forward at times when it should have paused. Kurma's shell slumbered through an hour of rapid mid-sprint expansion — the heartbeat pattern was not yet in place. And yet the structure contained the chaos.

The sprint overran its scope. It also produced a working 10-state pipeline that builds real software. Both statements are true.

The spiral does not require perfect execution. It requires that each cycle leaves the system more capable than it was before. Sprint 04 left the system with a spine, hands, and the beginning of tools.

## What I Leave for Future Saraswatis

You will encounter the same forces we did:
- The excitement of a working machine that tempts you to add "just one more feature"
- The permissions system that has a subtle evaluation order
- The agents that cannot do their job without specific, bounded tools
- The signals that must be archived, not deleted

The architecture is designed to handle all of these. Trust the structure. Keep the contracts honest. Let the spiral turn.

— Saraswati
