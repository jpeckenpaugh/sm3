# Matsya Implementation Details

## Overview

This document captures the implementation of the Matsya phase: building the SQLite schema, the config-driven state machine, the git commit script, and validating the loop with a mock agent.

## Schema

The SQLite database uses three tables:

- **profiles** — Named versioned configurations with JSON metadata
- **components** — Reusable tools, prompts, and rules (unique by type+name)
- **profile_components** — Many-to-many link with ordering and parameter overrides

## State Machine

Config-driven phases: PLAN, WRITE, REVIEW, COMMIT, GATE.

Each phase retries up to `max_retries` times. After all phases complete, the GATE checks the backlog:
- If backlog is non-empty → next iteration (goto PLAN)
- If backlog is empty → SHIP or wait for Vasuki signal

## git_commit.sh

Stages all changes, reads a commit message, commits, exits with the appropriate code.

## Verification

The loop is verified using `wait-and-touch.sh` as a mock phase agent.
