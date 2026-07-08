# Feature: `search_files` — Grep for the Pantheon

*A universal tool. Every agent needs it. No shell access required.*

---

## The Problem

No Spiral 1 agent can search the project. A scribe-PLAN wanting to find how a previous sprint handled a similar concept must know the exact file path. A builder-ENGINEER wanting to find the convention for endpoint naming must read files one-by-one by guessed path. A warden-REVIEW trying to verify that all error cases from the spec are handled in the implementation has no way to ask: *"find all references to this error code in src/"*

The agents have `read: allow` — but only for paths they already know. They cannot discover. They cannot search. They are blind to patterns across the project.

## The Tool

A custom tool at `.opencode/tools/search_files.ts` backed by `scripts/search_files.sh`.

### Interface

```typescript
tool({
  name: "search_files",
  description: "Search file contents using a literal or regex pattern",
  args: {
    pattern: tool.schema.string().describe("Search pattern (literal or regex)"),
    path: tool.schema.string().optional().default(".").describe("Root directory to search"),
    file_pattern: tool.schema.string().optional().describe("File glob pattern, e.g. '*.md' or '*.py'"),
    regex: tool.schema.boolean().optional().default(false).describe("Treat pattern as regex"),
    max_results: tool.schema.number().optional().default(50).describe("Maximum results to return"),
  },
  execute: async (args, context) => {
    // Invokes: bash scripts/search_files.sh <pattern> [--path <path>] [--include <glob>] [--regex] [--max <n>]
  }
})
```

### Return format

```json
{
  "matches": 3,
  "results": [
    {
      "file": "src/main.py",
      "line": 42,
      "content": "    def handle_error(code: str):"
    },
    {
      "file": "src/main.py",
      "line": 88,
      "content": "    if code == \"NOT_FOUND\":"
    }
  ],
  "truncated": false
}
```

If `max_results` is exceeded, `truncated` is `true` and the results contain the first N matches.

### Backing script: `scripts/search_files.sh`

```bash
#!/bin/bash
PATTERN="$1"
ROOT="${2:-.}"
INCLUDE="${3:-}"
REGEX="${4:-false}"
MAX="${5:-50}"

if [ "$REGEX" = "true" ]; then
  GREP_OPTS="-r -n"
else
  GREP_OPTS="-r -n -F"
fi

if [ -n "$INCLUDE" ]; then
  GREP_OPTS="$GREP_OPTS --include='$INCLUDE'"
fi

grep $GREP_OPTS "$PATTERN" "$ROOT" | head -n "$MAX"
```

### Permission

The tool is declared in base profiles so all derived agents inherit it:

```yaml
permission:
  "*": deny
  read: allow
  edit:
    "*.md": allow
    ...
  search_files: allow    # <-- single line
```

### What it enables

| Agent | Before | After |
|-------|--------|-------|
| scribe-PLAN | Reads files one-by-one searching for prior art | `search_files pattern:"error handling" file_pattern:*.md` → finds all relevant docs in one call |
| builder-ENGINEER | Guesses which module contains the helper function | `search_files pattern:"def format_date" file_pattern:*.py` → finds it instantly |
| warden-REVIEW | Reads entire spec and entire implementation to compare | `search_files pattern:"error_code" path:src/` → verifies all error cases are implemented |
| Any agent | Cannot find where a convention was established | `search_files pattern:"convention"` → finds the decision record |

## Backward Compatibility

If `.opencode/tools/search_files.ts` does not exist, the tool call is ignored. No crash, no error.

---

*Specified by Saraswati. Built by Matsya. Used by all Spiral 1 agents. Watched by Kurma.*
