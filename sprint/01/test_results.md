
═══════════════════════════════════════════════════════
  Sprint 01 — Automated Feature Tests
═══════════════════════════════════════════════════════

── ft001: Seed & Component Decomposition ──
  ✅ seed exits 0
  ✅ seed is idempotent (second run)
  ✅ 6 profiles seeded
  ✅ 13 components seeded
  ✅ 14 profile-component links
  ✅ ft001: Seed & Component Decomposition complete

── ft002: CLI Framework ──
  ✅ sm --help exits 0
  ✅ sm seed via sm.py
  ✅ sm list --help shows subcommands
  ✅ sm generate --help shows subcommands
  ✅ ft002: CLI Framework complete

── ft004: List Commands ──
  ✅ list profiles shows scribe
  ✅ list profiles --json is valid JSON
  ✅ list profiles -v shows permissions
  ✅ list components shows obey-exactly
  ✅ list components --json is valid JSON
  ✅ list components -v shows full content
  ✅ ft004: List Commands complete

── ft006: Generate Agent ──
  ✅ generate agent scribe
  ✅ scribe agent file exists
  ✅ scribe agent has description
  ✅ scribe agent has mode
  ✅ scribe agent has temperature
  ✅ scribe agent has permissions
  ✅ scribe agent body has obey-exactly
  ✅ scribe agent body has preamble
  ✅ scribe agent body has domain
  ✅ generate agent builder
  ✅ builder agent file exists
  ✅ builder agent shares obey-exactly rule
  ✅ generate agent warden
  ✅ warden agent exists
  ✅ generate agent for missing profile exits non-zero
  ✅ ft006: Generate Agent complete

── ft005: Status Command ──
  ✅ status shows database ready
  ✅ status shows profile count
  ✅ status shows component count
  ✅ status shows assembly count
  ✅ ft005: Status Command complete

── ft003: Run Command ──
  ✅ run with missing profile exits non-zero
  ✅ run displays profile name
  ✅ run displays role
  ✅ run displays component count
  ✅ ft003: Run Command (loading verification) complete

── Variant Test (litmus) ──
  ✅ variant seed exits 0
  ✅ 7 profiles after adding variant
  ✅ 14 components after adding variant
  ✅ generate variant agent
  ✅ variant agent file exists
  ✅ variant agent uses obey-exactly
  ✅ variant agent uses scribe-preamble
  ✅ variant agent has new domain content
  ✅ original scribe unchanged
  ✅ Variant Test: no duplication of existing data

═══════════════════════════════════════════════════════
  Results
═══════════════════════════════════════════════════════
  Passed: 54
  Failed: 0

  All tests passed. Sprint 01 is verified.

