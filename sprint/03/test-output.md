
═══════════════════════════════════════════════════════
  Sprint 03 — Automated Feature Tests
═══════════════════════════════════════════════════════

── ft001: Schema — pipeline tables ──
  ✅ pipeline_states table exists
  ✅ pipeline_transitions table exists
  ✅ file_contracts table exists
  ✅ phase_events table exists
  ✅ phase_events index exists

── ft002: Pipeline seeds ──
  Pipeline: 5 states, 6 transitions, 9 contracts seeded.
  ✅ seed_pipeline_tables runs without error
  ✅ seed data correct (5 states, 6 transitions, 9+ contracts)

── ft003: Phase events (ft015) ──
OK
  ✅ log_phase_event and read_phase_events work
OK
  ✅ read_phase_events as_json=True works

── ft004: Engine — transition resolution ──
OK
  ✅ transition resolution correct

── ft005: Engine — guard evaluation ──
OK
  ✅ guard evaluation correct

── ft006: File contracts (ft012) ──
OK
  ✅ contract verification and manifest writing work

── ft007: Escalation mechanism (ft013) ──
OK
  ✅ escalation detection works

── ft008: Backward compatibility ──
OK
  ✅ _has_pipeline_tables detects pipeline schema
OK
  ✅ _has_pipeline_tables returns False for old DB

═══════════════════════════════════════════════════════
  Results
═══════════════════════════════════════════════════════
  Passed: 15
  Failed: 0

  All tests passed. Sprint 03 is verified.
