=== Sprint 07 Verification Suite ===

--- 1. Generator module imports ---
OK
  ✅ generator.py imports cleanly

--- 2. sm generate agent backward compatibility ---
✓ Generated 16/16 agent files.
  ⚠ Difference in builder-TEST.md (may be expected if agents were stale)
  ⚠ Difference in warden-GATE.md (may be expected if agents were stale)
  ⚠ Difference in warden-TEST_RUN.md (may be expected if agents were stale)
  ✅ No raw <MODE_FLAG> in freshly generated agents

--- 3. sm init produces correct agent files ---
  Next steps:
    sm seed                  Load agent profiles from local seed data
    sm list profiles         See available profiles
    sm run --profile <name>  Start a state machine sprint
    sm --help                Show all commands
  ✅ No raw <MODE_FLAG> in any generated agent file

--- 4. Inheritance resolution ---
    sm list profiles         See available profiles
    sm run --profile <name>  Start a state machine sprint
    sm --help                Show all commands
  ✅ scribe-PLAN has full inheritance chain

--- 5. Mode flag substitution ---
    sm list profiles         See available profiles
    sm run --profile <name>  Start a state machine sprint
    sm --help                Show all commands
  ✅ All derived profiles have correct mode flags

--- 6. Output parity (init vs generate) ---
    sm list profiles         See available profiles
    sm run --profile <name>  Start a state machine sprint
    sm --help                Show all commands
✓ Generated 16/16 agent files.
  ✅ All agent files identical between init and generate paths

=== Results: 6 passed, 0 failed ===
All tests passed. Sprint 07 is verified.
