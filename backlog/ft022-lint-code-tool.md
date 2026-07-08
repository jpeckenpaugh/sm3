# Feature: `lint_code` — Catch Errors Before Tests

*A domain-specific tool for builder-ENGINEER. Static analysis without execution.*

---

## The Problem

builder-ENGINEER writes Python code but cannot run it. The only verification available is `check_syntax`, which confirms the AST parses — but tells the builder nothing about:
- Unused imports
- Undefined variables
- Unreachable code
- Style violations (PEP 8)
- Common bug patterns

These issues are only discovered later when warden-TEST_RUN tries to execute the tests and fails. That wastes an iteration cycle: engineer writes code → test builds tests → test runner discovers a basic lint error → escalation → retry.

A lint tool would catch these issues in the builder's own pass, before the code ever reaches a test phase.

## The Tool

A custom tool at `.opencode/tools/lint_code.ts` backed by `scripts/lint_code.sh`.

### Interface

```typescript
tool({
  name: "lint_code",
  description: "Run static analysis on a Python file without executing it",
  args: {
    file_path: tool.schema.string().describe("Path to the Python file to lint"),
    rules: tool.schema.array(tool.schema.string()).optional().describe("Specific rules to check (e.g. ['E', 'F', 'W'])"),
  },
  execute: async (args, context) => {
    // Invokes: bash scripts/lint_code.sh <file_path> [--rules <codes>]
  }
})
```

### Return format

```json
{
  "file": "src/main.py",
  "valid": false,
  "issues": [
    {
      "line": 10,
      "column": 5,
      "code": "F401",
      "message": "'os' imported but unused",
      "severity": "warning"
    },
    {
      "line": 42,
      "column": 12,
      "code": "E302",
      "message": "Expected 2 blank lines after class definition",
      "severity": "style"
    },
    {
      "line": 88,
      "column": 1,
      "code": "F821",
      "message": "Undefined name 'handle_error'",
      "severity": "error"
    }
  ],
  "error_count": 1,
  "warning_count": 1,
  "style_count": 1
}
```

### Backing script: `scripts/lint_code.sh`

```bash
#!/bin/bash
FILE="$1"
shift

if [ ! -f "$FILE" ]; then
  echo '{"error": "File not found: '"$FILE"'"}'
  exit 1
fi

# Prefer pyflakes for fast, focused analysis (covers F-codes: undefined names, unused imports)
if command -v pyflakes &> /dev/null; then
  pyflakes "$FILE" 2>&1
  exit ${PIPESTATUS[0]}
fi

# Fallback: use python3 -m py_compile (same as check_syntax, but with more detail)
python3 -c "
import ast, sys, py_compile
try:
    py_compile.compile('$FILE', doraise=True)
except py_compile.PyCompileError as e:
    print(f'{{ \"error\": \"{e}\" }}')
    sys.exit(1)
" 2>&1
```

### Permission

Added to builder profiles alongside `check_syntax`:

```yaml
permission:
  "*": deny
  read: allow
  edit:
    "*.py": allow
    "*.sh": allow
    ...
  check_syntax: allow
  lint_code: allow         # <-- added
```

## Integration with ENGINEER Mode

```markdown
### 4. Verify

After writing each source file, call `lint_code` with the file path.
Fix all errors (F-codes) before proceeding. Warnings and style issues
should be fixed but are not blocking.

Only proceed to OUTPUT after all files pass linting without errors.
```

## What it enables

| Before | After |
|--------|-------|
| builder-ENGINEER writes code blind to basic errors | builder-ENGINEER lints each file after writing, catching undefined names and unused imports immediately |
| Lint errors discovered by warden-TEST_RUN cost a full iteration cycle | Lint errors caught in ENGINEER phase, fixed before tests are written |
| `check_syntax` only validates the AST parses | `lint_code` catches semantic issues the parser cannot see |

## Non-Goals

- Installing lint tools (assumes `pyflakes` or `py_compile` is available)
- Auto-fixing issues (the agent reads the report and fixes them itself)
- Running in the background (called explicitly by the agent after writing)

---

*Specified by Saraswati. Built by Matsya. Used by builder-ENGINEER and builder-TEST. Watched by Kurma.*
