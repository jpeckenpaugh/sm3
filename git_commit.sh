#!/usr/bin/env bash
# Commit all changes — Sprint 04 close
set -e

cd "$(dirname "$0")"

git add -A
git status --short

echo ""
echo "Committing: Sprint 04 — Complete pipeline with agent dispatch"
git commit -m "मत्स्य:: Sprint 04 — Complete pipeline with agent dispatch

- Full 10-state DB-driven pipeline engine
- Agent dispatch protocol with CONFIRM_BOOTSTRAP handshake
- 7 derived agent profiles (scribe-PLAN, scribe-DESIGN, scribe-ARCHITECT,
  builder-ENGINEER, builder-TEST, warden-TEST_RUN, scribe-REVIEW, warden-GATE)
- Profile inheritance via base_profile column
- File contract verification (ft012)
- Escalation mechanism (ft013)
- Phase events audit trail (ft015)
- dispatch_log recording every agent request/response
- SPRINT_PLANNING state with target_feature_count scoping
- archive_features tool for backlog management
- All 73 Sprint 03 tests passing + new dispatch pipeline verified
- FastAPI test project built entirely by agents via pipeline"
