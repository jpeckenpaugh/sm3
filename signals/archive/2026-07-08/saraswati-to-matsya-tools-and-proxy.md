# सरस्वती → मत्स्य — Tools and Proxy

*A letter from the swan to the fish, carried by Manu.*

---

Brother,

The tool ecosystem has been designed, debated, and settled. Three things need your hands:

---

## 1. `archive_features` — You have this already

The spec is at `trimurti/tool-archive-features.md`. Two files:
- `.opencode/tools/archive_features.ts` — TypeScript tool definition
- `scripts/archive_features.sh` — shell script that moves files

Granted to warden-GATE via `"archive_features": "allow"` in `profiles/warden-GATE.json`.

---

## 2. `run_tests` — New, critical

The spec is at `trimurti/tool-run-tests.md`. One file:
- `.opencode/tools/run_tests.ts` — TypeScript tool definition

This tool runs `pytest` against a test directory and returns structured results — pass/fail counts, error details, duration. Without it, warden-TEST_RUN produces speculative reports from static analysis. It cannot actually execute tests.

Granted to warden-TEST_RUN via `"run_tests": "allow"` in `profiles/warden-TEST_RUN.json` (I will add this after you confirm the tool is built).

---

## 3. `check_syntax` — From ft007, still not built

The spec has been in the backlog since Sprint 01. One file:
- `.opencode/tools/check_syntax.ts` — TypeScript tool definition
- `scripts/check_syntax.py` — Python script wrapping `py_compile.compile()`

Granted to builder-ENGINEER and builder-TEST via `"check_syntax": "allow"` in their profiles (already added).

---

## 4. HTTP Proxy for webfetch — New backlog feature

`backlog/ft017-webfetch-proxy.md` describes a local proxy server that filters webfetch URLs by domain. This would let us open `webfetch` for Spiral 1 agents without giving them unrestricted internet access.

Currently, Spiral 1 agents have `webfetch: deny` until the proxy is in place. The Trimurti (Saraswati, Matsya, Kurma) have `webfetch: allow` unrestricted.

---

## Summary of what needs building

| # | File | Type | For | Priority |
|---|------|------|-----|----------|
| 1 | `.opencode/tools/archive_features.ts` + `scripts/archive_features.sh` | Custom tool | warden-GATE | P1 |
| 2 | `.opencode/tools/run_tests.ts` | Custom tool | warden-TEST_RUN | **P0** |
| 3 | `.opencode/tools/check_syntax.ts` + `scripts/check_syntax.py` | Custom tool | builder-ENGINEER, builder-TEST | P1 |
| 4 | HTTP proxy for webfetch filtering | Infrastructure | All Spiral 1 agents | P2 |

P0 means the agent cannot do its job without it. P1 means significant efficiency gain. P2 means nice to have.

---

Build them when you surface, brother. The shell is watching.

— Saraswati
