# Feature: Check Syntax Tool

*A concept for the Builder to interpret.*

---

## The Problem

The Builder writes Python code but has no way to verify it is syntactically valid before submitting. A misplaced indentation, missing bracket, or unbalanced paren causes the VERIFY phase to fail, triggering a retry and slowing the sprint. The Builder needs a well-formedness check on their own output without crossing the line into test execution.

## The Boundary

The Builder should be able to **confirm their code parses** without being able to **run their code**. Syntax verification is to code what spell-check is to prose — a surface-level well-formedness gate, not a semantic validation.

Giving the Builder direct `python` execution permission blurs the line between Builder and Tester. A dedicated tool with a narrow scope preserves the separation.

## The Goal

A `check_syntax` tool that accepts a Python file path and returns:

- `{ "valid": true }` if the file parses without syntax errors
- `{ "valid": false, "error": "IndentationError at line 42", "line": 42 }` if a syntax error is found

The tool does nothing else. It does not import the file. It does not execute functions. It does not discover tests. It parses for structure only.

## The Shape

The tool is a thin wrapper around Python's built-in `py_compile` module or `compile()` builtin:

```
check_syntax <filepath>
```

Implementation sketch (underlying implementation, not the Builder's code):

```python
import py_compile
import sys

def check_syntax(filepath):
    try:
        py_compile.compile(filepath, doraise=True)
        return { "valid": True }
    except py_compile.PyCompileError as e:
        return { "valid": False, "error": str(e) }
```

The tool is invoked by the Builder through a profile permission, not by direct shell access. The Builder's profile is updated to include:

```yaml
# in permissions:
tool:
  check_syntax: allow
```

No `bash: allow`, no `subprocess`, no `python: allow`. Just this single narrow tool.

## What This Sprint Must Deliver

1. The `check_syntax` tool script (a standalone executable or a callable module)
2. An update to the Builder's profile seed data to include the `tool: { check_syntax: allow }` permission
3. An update to the generated agent file template (if `sm generate agent` is already implemented) to include the tool permission in the YAML frontmatter

## Non-Goals

- Running tests
- Type checking
- Linting beyond syntax (no pyflakes, pylint, mypy, etc.)
- Formatting or auto-fixing code
- Checking multiple files in one invocation

## Open Questions

1. Should the tool accept multiple file paths in one call, or is single-file sufficient?
2. Should it output JSON (for programmatic consumption) or plain text (for human reading)? JSON is preferred for consistency with other tools.
3. Should the tool be written in Python (stdlib only) or shell? Python is more portable and avoids shell injection concerns.

---

*The Scribe maps the territory. The Builder walks it.*

*Added by the Warden after review:* This tool sets a pattern for future narrow-scope tools (check-links, archive-snapshot, run-test-suite). Each is a named permission, not an ambient capability.
