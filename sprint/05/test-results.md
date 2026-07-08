=== Sprint 05 Verification Suite ===

--- 1. Seed Order (ft029) ---
  ✅ No 'Base profile not found' warnings during seed

--- 2. Zombie Columns Removed (ft026) ---
  ✅ 'body' column removed from profiles table
  ✅ 'preamble' column removed from profiles table

--- 3. Permission Merge (ft024) ---
  ✅ scribe-PLAN inherits search_files from base
  ✅ builder-ENGINEER inherits list_files from base
  ✅ warden-GATE inherits file_tree from base
  ✅ scribe-PLAN has read_pulse from derived profile
  ✅ builder-ENGINEER has lint_code from derived profile
  ✅ warden-REVIEW has compare_files from derived profile

--- 4. Bootstrap Protocol (ft025) ---
  ✅ scribe-PLAN has CONFIRM_BOOTSTRAP section
  ✅ scribe-PLAN mode flag correctly substituted to PLAN
  ✅ warden-GATE mode flag correctly substituted to SPRINT_GATE
  ✅ No raw <MODE_FLAG> placeholders in any generated agent file

--- 5. Auto-Orientation ---
  ✅ scribe-mode-plan includes file_tree orientation
  ✅ scribe-mode-design includes file_tree orientation
  ✅ scribe-mode-architect includes file_tree orientation
  ✅ scribe-mode-review includes file_tree orientation
  ✅ scribe-mode-sprint-planning includes file_tree orientation
  ✅ builder-mode-engineer includes file_tree orientation
  ✅ builder-mode-test includes file_tree orientation
  ✅ warden-mode-review includes file_tree orientation
  ✅ warden-mode-test-run includes file_tree orientation
  ✅ warden-mode-gate includes file_tree orientation

--- 6. Generate All Agents (ft027) ---
  ✅ sm generate agents produced 19 agent files (target: 16+)
  ✅ 5 legacy agent files archived

--- 7. Universal Tools ---
  ✅ search_files validates empty pattern
  ✅ search_files returns structured JSON with matches
  ✅ list_files returns structured JSON with count
  ✅ file_tree shows directory structure

--- 8. Domain Tools ---
  ✅ compare_files correctly identifies identical files
  ✅ lint_code validates clean Python file
  ✅ read_pulse returns sprint data

--- 9. Fleet Dashboard ---
  ✅ Dashboard files exist
  ✅ Dashboard has multi-DB config support

--- 10. Pytest at Init ---
  ✅ sm init has pytest auto-install code

=== Results: 35 passed, 0 failed ===
