# Feature: `list_files` — Discover What Exists

*A universal tool. The companion to search_files. Agents should not guess paths.*

---

## The Problem

Agents work with explicitly named paths. A scribe-PLAN told to read "all backlog features" must be given the exact glob pattern. A builder-ENGINEER told to "list all files in src/" cannot — there is no tool that returns a directory listing. A warden-GATE evaluating whether the backlog is empty must count features by reading the directory path.

The agents have `read: allow` for file contents but no way to enumerate what files exist. They navigate the project blind, guessing paths, hoping files are where they expect them to be.

## The Tool

A custom tool at `.opencode/tools/list_files.ts` backed by `scripts/list_files.sh`.

### Interface

```typescript
tool({
  name: "list_files",
  description: "List files and directories matching a glob pattern",
  args: {
    pattern: tool.schema.string().describe("Glob pattern, e.g. 'backlog/*.md' or 'src/**/*.py'"),
    root: tool.schema.string().optional().default(".").describe("Root directory"),
    max_results: tool.schema.number().optional().default(200).describe("Maximum entries to return"),
  },
  execute: async (args, context) => {
    // Invokes: bash scripts/list_files.sh <pattern> [--root <path>] [--max <n>]
  }
})
```

### Return format

```json
{
  "files": [
    "backlog/ft001-seed-decomposition.md",
    "backlog/ft002-cli-framework.md",
    "backlog/ft003-run-command.md"
  ],
  "count": 18,
  "truncated": false
}
```

### Backing script: `scripts/list_files.sh`

```bash
#!/bin/bash
PATTERN="$1"
ROOT="${2:-.}"
MAX="${3:-200}"

cd "$ROOT"
find . -path "./$PATTERN" -type f 2>/dev/null | head -n "$MAX"
```

### Permission

Added to every base profile alongside `search_files`:

```yaml
permission:
  "*": deny
  read: allow
  ...
  search_files: allow
  list_files: allow       # <-- added
```

### What it enables

| Agent | Before | After |
|-------|--------|-------|
| scribe-PLAN | Given "read all features in backlog/" — must guess the exact filenames | `list_files pattern:"backlog/ft-*.md"` → sees all 18 feature files |
| builder-ENGINEER | Told "review existing modules in src/" — guesses paths | `list_files pattern:"src/**/*.py"` → sees the full module tree |
| warden-GATE | Evaluates backlog emptiness by reading individual files | `list_files pattern:"backlog/ft-*.md"` → count tells the story |
| Any agent | Discovers project structure by error (tries a path, gets nothing, tries another) | `list_files` on first call orients the agent immediately |

## Auto-run on Session Start

The markdown mode-specific instructions in each derived profile should include an orientation step:

```markdown
### On Session Start

Before beginning your work, orient yourself:
- Call `list_files` with `pattern="**/*"` to see the project structure
- Call `search_files` to find relevant prior work if needed
- Then proceed with your assigned mode's work
```

This can be added to the mode-specific component content for all agents.

---

*Specified by Saraswati. Built by Matsya. Used by all Spiral 1 agents. Watched by Kurma.*
