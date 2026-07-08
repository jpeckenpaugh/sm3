"""
pipeline/dispatch.py — Agent dispatch via opencode CLI.

Dispatches work to OpenCode agents using the `opencode run --format json`
CLI command. Supports the CONFIRM_BOOTSTRAP handshake protocol and the
INPUT/OUTPUT path convention from ft016.

Usage:
    from pipeline.dispatch import dispatch_sync, handshake_sync
"""

import json
import os
import re
import sqlite3
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Optional


# ─── Data types ──────────────────────────────────────────────────────────────

@dataclass
class DispatchResult:
    session_id: str
    response_text: str
    confirmed_modes: list[str]


# ─── Response parsing (from fallen machine, daemon.py lines 396-423) ────────

def _extract_response_text(response: str) -> str:
    """Extract text content from a raw opencode CLI response."""
    # The CLI returns JSON-lines; extract text parts
    texts = []
    for line in response.strip().split("\n"):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            if data.get("type") == "text":
                text = data.get("part", {}).get("text", "")
                if text:
                    texts.append(text)
        except json.JSONDecodeError:
            # Fallback: include non-JSON lines as-is
            texts.append(line)
    return "\n".join(texts)


def _parse_confirmed_modes(text: str) -> list[str]:
    """Extract mode flags from a CONFIRM_BOOTSTRAP response.

    Matches patterns like:
      "Available MODE_FLAG values are CONFIRM_BOOTSTRAP, REVIEW"
      "Mode flags: CONFIRM_BOOTSTRAP, DESIGN"
    """
    match = re.search(
        r"(?:Mode flags:\s*|Available MODE_FLAG values are\s*)([\w\s,]+)",
        text,
    )
    if not match:
        return []
    raw = match.group(1).strip().rstrip(".")
    return [m.strip() for m in raw.split(",") if m.strip()]


# ─── CLI invocation ─────────────────────────────────────────────────────────

def _run_opencode(
    agent: str,
    message: str,
    project_dir: str = ".",
    timeout: int = 120,
) -> str:
    """Run `opencode run --agent <name> --format json <message>`.

    Returns the raw stdout text.
    """
    cmd = [
        "opencode", "run",
        "--agent", agent,
        "--format", "json",
        message,
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=os.path.abspath(project_dir),
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"opencode exited {result.returncode} for agent '{agent}': "
            f"{result.stderr[:500]}"
        )
    return result.stdout


def _extract_session_id(raw: str) -> Optional[str]:
    """Extract the session ID from JSON-lines output."""
    for line in raw.strip().split("\n"):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            sid = data.get("sessionID")
            if sid:
                return sid
        except json.JSONDecodeError:
            continue
    return None


# ─── Public API ──────────────────────────────────────────────────────────────

def handshake_sync(
    agent_name: str,
    project_dir: str = ".",
    timeout: int = 120,
) -> DispatchResult:
    """Perform the CONFIRM_BOOTSTRAP handshake with an agent.

    Returns the session ID, response text, and list of confirmed mode flags.
    """
    raw = _run_opencode(agent_name, "CONFIRM_BOOTSTRAP", project_dir, timeout)
    session_id = _extract_session_id(raw)
    response_text = _extract_response_text(raw)
    confirmed_modes = _parse_confirmed_modes(response_text)

    return DispatchResult(
        session_id=session_id or "unknown",
        response_text=response_text,
        confirmed_modes=confirmed_modes,
    )


def dispatch_sync(
    agent_name: str,
    request_text: str,
    project_dir: str = ".",
    timeout: int = 600,
) -> DispatchResult:
    """Send work to an agent and return the response.

    The request_text should follow the convention:
      <MODE_FLAG> INPUT1:<path> OUTPUT:<path>

    This function does NOT perform the handshake — call handshake_sync()
    first to establish the session, then use the same agent for work.
    """
    raw = _run_opencode(agent_name, request_text, project_dir, timeout)
    session_id = _extract_session_id(raw)
    response_text = _extract_response_text(raw)

    return DispatchResult(
        session_id=session_id or "unknown",
        response_text=response_text,
        confirmed_modes=[],  # not returned from work dispatch
    )


# ─── Request text builder (from ft016) ───────────────────────────────────────

def build_request(
    state_name: str,
    sprint_number: int,
    contracts: list[dict],
) -> str:
    """Build request text: <MODE_FLAG> INPUT1:<path> OUTPUT:<path> ...

    contracts is a list of dicts with keys: direction, pattern, template, description.
    The template column uses {:03d} format and is resolved with the sprint number.
    Falls back to the pattern column if no template is set.

    Inputs are always numbered (INPUT1, INPUT2, ...).
    If there's a single output it uses OUTPUT:; multiple use OUTPUT1:, OUTPUT2:, ...
    """
    parts = [state_name]

    input_patterns = [c for c in contracts if c["direction"] == "input"]
    output_patterns = [c for c in contracts if c["direction"] == "output"]

    for i, c in enumerate(input_patterns, 1):
        tmpl = c.get("template") or c["pattern"]
        resolved = tmpl.replace("{:03d}", f"{sprint_number:03d}") if "{:03d}" in tmpl else tmpl
        parts.append(f"INPUT{i}:{resolved}")

    for i, c in enumerate(output_patterns, 1):
        tmpl = c.get("template") or c["pattern"]
        resolved = tmpl.replace("{:03d}", f"{sprint_number:03d}") if "{:03d}" in tmpl else tmpl
        output_prefix = "OUTPUT" if len(output_patterns) == 1 else f"OUTPUT{i}"
        parts.append(f"{output_prefix}:{resolved}")

    return " ".join(parts)


# ─── Dispatch logging ────────────────────────────────────────────────────────

def record_dispatch(
    conn: sqlite3.Connection,
    sprint_id: int,
    session_id: str,
    agent_name: str,
    request_text: str,
    response_text: str,
    status: str = "completed",
) -> None:
    """Insert a row into the dispatch_log table."""
    conn.execute(
        """INSERT INTO dispatch_log
           (sprint_id, session_id, agent_name, request_text, response_text, status, completed_at)
           VALUES (?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))""",
        (sprint_id, session_id, agent_name, request_text, response_text, status),
    )
    conn.commit()
