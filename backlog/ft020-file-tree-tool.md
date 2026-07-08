# Feature: `file_tree` — Project Structure at a Glance

*A universal orientation tool. Agents should see the shape before they touch the content.*

---

## The Problem

`list_files` returns a flat list of matching paths. It is excellent for finding specific files but poor for understanding the *shape* of the project — which directories exist, how deep the tree goes, what modules sit where, which sprints have been completed.

A new agent entering a container needs a mental model of the project layout before it can navigate effectively. Reading a flat list of 59 files (as the project root currently has) is slower than seeing a tree.

## The Tool

A custom tool at `.opencode/tools/file_tree.ts` backed by `scripts/file_tree.sh`.

### Interface

```typescript
tool({
  name: "file_tree",
  description: "Show the directory tree structure, optionally filtered by depth",
  args: {
    root: tool.schema.string().optional().default(".").describe("Root directory"),
    depth: tool.schema.number().optional().default(3).describe("Maximum depth to display"),
    dirs_only: tool.schema.boolean().optional().default(false).describe("Show directories only"),
    pattern: tool.schema.string().optional().describe("Filter to files matching glob pattern"),
  },
  execute: async (args, context) => {
    // Invokes: bash scripts/file_tree.sh [--root <path>] [--depth <n>] [--dirs-only] [--pattern <glob>]
  }
})
```

### Return format

```text
.
├── backlog/
│   ├── ft001-seed-decomposition.md
│   ├── ft002-cli-framework.md
│   └── ...
├── components/
│   ├── prompts/
│   │   ├── builder-domain.json
│   │   ├── builder-mode-engineer.json
│   │   └── ...
│   └── rules/
├── pipeline/
│   ├── engine.py
│   ├── dispatch.py
│   ├── events.py
│   ├── contracts.py
│   └── seeds.py
├── profiles/
│   ├── builder-ENGINEER.json
│   ├── builder-TEST.json
│   └── ...
├── sprint/
│   ├── 001/
│   │   ├── brief.md
│   │   └── ...
│   └── 002/
├── src/
│   └── genesis_sm/
│       ├── __init__.py
│       ├── cli.py
│       ├── pipeline/
│       └── ...
└── ...
```

### Backing script: `scripts/file_tree.sh`

```bash
#!/bin/bash
ROOT="${1:-.}"
DEPTH="${2:-3}"
shift 2

cd "$ROOT"
tree -L "$DEPTH" --charset=utf-8 "$@"
```

If `tree` is not installed, fall back to `find`:

```bash
find . -maxdepth "$DEPTH" -type f -o -type d | sort
```

### Permission

```yaml
permission:
  "*": deny
  ...
  search_files: allow
  list_files: allow
  file_tree: allow       # <-- added
```

### Auto-run on Session Start

The mode-specific instruction for every agent should include this as the first step:

```markdown
### 1. Orient

Before beginning your assigned work, call `file_tree` with `depth=2` to
see the project structure. Then call `list_files` with your relevant
pattern to find the specific files you need.
```

## What it enables

| Agent | Before | After |
|-------|--------|-------|
| **Any new agent** | Enters blind, must piece together the project structure by trial and error | Sees the full shape in one call, knows where everything lives |
| **builder-ENGINEER** | Does not know whether `src/` has a flat or nested module structure | `file_tree path:src/ depth:2` → sees the module layout immediately |
| **warden-REVIEW** | Must guess which sprints exist and what artifacts they contain | `file_tree path:sprint/ depth:2` → sees all sprint directories at a glance |

---

*Specified by Saraswati. Built by Matsya. Used by all Spiral 1 agents. Watched by Kurma.*
