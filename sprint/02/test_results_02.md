
═══════════════════════════════════════════════════════
  Sprint 02 — Automated Feature Tests
═══════════════════════════════════════════════════════

── ft001: Schema — sprints + phase_runs tables ──
  ✅ seed creates database
  ✅ sprints table exists
  ✅ phase_runs table exists
  ✅ sprints has number column
  ✅ phase_runs has sprint_id column
  ✅ ft001: Schema tables verified

── ft003: sm log (no data) ──
  ✅ sm log shows empty message
  ✅ sm log --json shows empty array
  ✅ ft003: Empty log display verified

── ft004: sm sprint subcommands ──
  ✅ sprint start --number 1 --mode manual
  ✅ sprint 1 exists in DB
  ✅ sprint start --number 2
  ✅ sprint start duplicate exits non-zero
  ✅ sprint note --number 1
  ✅ sprint 1 has note
  ✅ sprint complete --number 1
  ✅ sprint 1 status is completed
  ✅ sprint fail --number 2 --reason
  ✅ sprint 2 status is failed
  ✅ sprint note on missing sprint exits non-zero
  ✅ sprint complete on missing sprint exits non-zero
  ✅ ft004: Sprint lifecycle verified

── ft003: sm log (with data) ──
  ✅ sm log shows sprint 1
  ✅ sm log shows sprint 2
  ✅ sm log --sprint 1 filters
  ✅ sm log --sprint 1 excludes sprint 2
  ✅ sm log --json is valid JSON
  ✅ sm log --json shows mode
  ✅ sm log --json --sprint 2
  ✅ manual sprint shows no phase log
  ✅ ft003: Log display verified

── ft005: sm init ──
  ✅ sm init fresh project
  ✅ database file exists
  ✅ backlog directory exists
  ✅ sprint directory exists
  ✅ agents directory exists
  ✅ .sm-config.json exists
  ✅ .sm-config.json has db_path
  ✅ profiles seeded in init
  ✅ scribe agent generated
  ✅ scribe agent has frontmatter
  ✅ registry has project
  ✅ default project set
  ✅ ft005: Project init verified

── ft009: Sprint 01 adoption ──
  ✅ sm init with adoption
  ✅ adopted sprint 1 exists
  ✅ adopted sprint is manual
  ✅ adopted sprint is completed
  ✅ ft009: Sprint 01 adoption verified

── ft002: State machine phase logging ──
  ✅ sm run writes phase logs
  ✅ phase_runs rows exist
  ✅ sprint auto-created
  ✅ auto-created sprint is driven
  ✅ phase_runs have valid statuses
  ✅ log --phases shows phases
  ✅ ft002: State machine logging verified

── ft006: Project registry ──
  ✅ list projects shows test-fresh
  ✅ list projects --json is valid
  ✅ ft006: Registry display verified

── ft008: sm projects subcommands ──
  ✅ projects default sets default
  ✅ default project is test-fresh
  ✅ projects remove works
  ✅ registry no longer has test-adopt
  ✅ ft008: Project management verified

── ft007: .sm-config.json auto-discovery ──
  ❌ auto-discovery finds profiles
  ❌ auto-discovery uses correct db
  ✅ ft007: Auto-discovery verified

── Error handling ──
  ✅ log on missing DB shows message
  ✅ sprint on missing DB exits non-zero
  ✅ run on missing profile exits non-zero
  ✅ run on missing DB exits non-zero
  ✅ Error handling verified

═══════════════════════════════════════════════════════
  Results
═══════════════════════════════════════════════════════
  Passed: 70
  Failed: 2

  Some tests failed. Review output above.

