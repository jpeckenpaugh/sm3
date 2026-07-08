# Feature: `compare_files` — Spec vs. Implementation Verification

*A domain-specific tool for warden-REVIEW. The difference between guessing and knowing.*

---

## The Problem

warden-REVIEW's entire job is verifying that an implementation matches its specification. Currently it does this by reading both files in their entirety, holding them in context, and comparing them manually. This is:

- **Slow** — the agent must read two potentially large documents and keep both in context
- **Imprecise** — human-like reading misses subtle mismatches (a renamed field, a changed return type)
- **Unstructured** — the review report depends on what the agent happened to notice, not on a systematic diff

The warden needs a structured diff between spec and implementation — not to replace its judgment, but to *anchor* its judgment in concrete differences.

## The Tool

A custom tool at `.opencode/tools/compare_files.ts` backed by `scripts/compare_files.sh`.

### Interface

```typescript
tool({
  name: "compare_files",
  description: "Compare two files and return structural differences",
  args: {
    file_a: tool.schema.string().describe("First file path (e.g. the specification)"),
    file_b: tool.schema.string().describe("Second file path (e.g. the implementation)"),
    context_lines: tool.schema.number().optional().default(3).describe("Lines of context around differences"),
    mode: tool.schema.string().optional().default("unified").describe("Diff mode: unified, word, or summary"),
  },
  execute: async (args, context) => {
    // Invokes: bash scripts/compare_files.sh <file_a> <file_b> [--context <n>] [--mode <mode>]
  }
})
```

### Return format (unified mode)

```json
{
  "identical": false,
  "hunks": 2,
  "additions": 3,
  "deletions": 1,
  "diff": "--- a/spec.md\n+++ b/src/main.py\n@@ -10,3 +10,3 @@\n   Returns: 200 OK\n-  Response: { \"status\": \"ok\" }\n+  Response: { \"status\": \"success\" }\n",
  "summary": "2 hunks, 3 additions, 1 deletion"
}
```

### Return format (summary mode)

```json
{
  "identical": false,
  "hunks": 2,
  "additions": 3,
  "deletions": 1,
  "summary": "2 hunks, 3 additions, 1 deletion",
  "diff": null
}
```

The summary mode is useful when the warden just needs to know *whether* files differ before deciding to read the full diff.

### Backing script: `scripts/compare_files.sh`

```bash
#!/bin/bash
FILE_A="$1"
FILE_B="$2"
CONTEXT="${3:-3}"
MODE="${4:-unified}"

if [ ! -f "$FILE_A" ]; then
  echo '{"error": "File not found: '"$FILE_A"'"}'
  exit 1
fi
if [ ! -f "$FILE_B" ]; then
  echo '{"error": "File not found: '"$FILE_B"'"}'
  exit 1
fi

if [ "$MODE" = "summary" ]; then
  diff -q "$FILE_A" "$FILE_B" > /dev/null 2>&1
  if [ $? -eq 0 ]; then
    echo '{"identical": true}'
  else
    STATS=$(diff --stat "$FILE_A" "$FILE_B" 2>/dev/null || echo "")
    echo '{"identical": false, "hunks": 1, "summary": "'$STATS'"}'
  fi
else
  diff -u -U "$CONTEXT" "$FILE_A" "$FILE_B"
fi
```

### Permission

Added only to warden-REVIEW's profile:

```yaml
permission:
  "*": deny
  read: allow
  edit:
    "sprint/*/review.md": allow
    ".escalation/*": allow
  compare_files: allow    # <-- warden-REVIEW only
```

This tool is **not** added to base profiles. It belongs only to the warden domain because comparing files is the warden's specific duty, not a universal capability.

## Integration with REVIEW Mode

The warden-REVIEW mode instructions should reference the tool:

```markdown
### 2. Verify Implementation

Call `compare_files` with:
  file_a: the specification path (from INPUT1)
  file_b: the implementation path (from INPUT2)
  mode: "summary"

If the files differ, call `compare_files` again with mode: "unified"
to see the specific differences. Use the diff output to anchor
your review report — note each mismatch, its location, and whether it
is a bug, a deviation, or an improvement.
```

## What it enables

| Before | After |
|--------|-------|
| warden-REVIEW reads spec and implementation in full, compares in context | warden-REVIEW calls `compare_files summary` first, then reads only the specific diffs |
| Review quality depends on what the agent noticed | Review is anchored to a systematic diff — nothing is missed |
| Subtle mismatches (renamed fields, changed return types) are easily overlooked | Every line-level difference is captured and presented |

---

*Specified by Saraswati. Built by Matsya. Used by warden-REVIEW. Watched by Kurma.*
