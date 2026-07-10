# Debug 05: Eliminate Shell Scripts — Pure TypeScript Tools

*The shell scripts introduced every quoting bug. TypeScript can do everything they do without the indirection.*

---

## The Diagnosis

Every tool is a chain of two files: `.ts` → `.sh` → utility. The `.ts` file builds a **string** and passes it to `Bun.$`:

```typescript
// Current pattern — builds a string, passes to shell
let cmd = `bash ${scriptPath} ${JSON.stringify(args.pattern)}`;
const result = await Bun.$`${cmd}`.text();
```

The shell script then parses the string arguments, handles quoting, calls utilities, and hand-rolls JSON. This is where the bugs live — every tool has shell quoting errors.

**The fix:** Remove the `.sh` file. Move the logic into the `.ts` file. Use `Bun.$` with **argument arrays** (which avoid shell quoting entirely) or pure TypeScript.

---

## The Pattern

Each tool becomes a single file at `.opencode/tools/<name>.ts`:

```typescript
import { tool } from "@opencode-ai/plugin";

export default tool({
  description: "...",
  args: { ... },
  async execute(args, context) {
    // 1. Validate
    // 2. Execute (via Bun.$ with array args, or pure TS)
    // 3. Return structured result
  },
});
```

Use `Bun.$` with an **array** for shell commands. An array passes each element as a separate argument — no shell quoting, no injection, no parsing:

```typescript
// ✅ Correct — array arguments, no shell parsing
const result = await Bun.$`grep -r -n --include ${args.file_pattern} ${args.pattern} ${root}`.text();
```

Each `${...}` in the template literal becomes a single argument, regardless of spaces or special characters. This is fundamentally different from building a string and passing it as `${cmd}`.

For pure TypeScript operations (reading files, walking directories), use `fs` and `path` directly without any shell call.

---

## Tool-by-Tool Specification

### 1. `search_files.ts` — Pure `Bun.$` with array args

```typescript
import { tool } from "@opencode-ai/plugin";
import path from "path";

export default tool({
  description: "Search file contents using a literal or regex pattern",
  args: {
    pattern: tool.schema.string().describe("Search pattern (literal or regex)"),
    path: tool.schema.string().optional().default(".").describe("Root directory to search"),
    file_pattern: tool.schema.string().optional().describe("File glob pattern, e.g. '*.md' or '*.py'"),
    regex: tool.schema.boolean().optional().default(false).describe("Treat pattern as regex"),
    max_results: tool.schema.number().optional().default(50).describe("Maximum results to return"),
  },
  async execute(args, context) {
    const root = args.path || ".";
    const grepArgs = ["-r", "-n"];
    if (args.file_pattern) grepArgs.push("--include", args.file_pattern);
    if (!args.regex) grepArgs.push("-F");
    grepArgs.push(args.pattern, root);

    const result = await Bun.$`grep ${grepArgs} ${root}`.text();
    // Parse grep output, return JSON
    const lines = result.trim().split("\n").filter(Boolean);
    const results = lines.slice(0, args.max_results).map(line => {
      const sepIndex = line.indexOf(":");
      const file = line.substring(0, sepIndex);
      const rest = line.substring(sepIndex + 1);
      const lineNum = parseInt(rest, 10) || 0;
      const content = rest.substring(rest.indexOf(":") + 1);
      return { file, line: lineNum, content };
    });
    return JSON.stringify({
      matches: results.length,
      results,
      truncated: lines.length > args.max_results,
    });
  },
});
```

**No `.sh` file needed.** `grep` arguments are passed as array elements — no quoting issues.

---

### 2. `read_pulse.ts` — Pure TypeScript via `Bun.sqlite` or `Bun.$`

```typescript
import { tool } from "@opencode-ai/plugin";
import path from "path";
import fs from "fs";

export default tool({
  description: "Read the pulse history of the container from the database",
  args: {
    db_path: tool.schema.string().optional().describe("Path to matsya.db (auto-detected if not provided)"),
  },
  async execute(args, context) {
    let dbPath = args.db_path;
    if (!dbPath) {
      const candidates = ["matsya.db", "test-project.db"];
      for (const c of candidates) {
        if (fs.existsSync(c)) { dbPath = c; break; }
      }
    }
    if (!dbPath) {
      return JSON.stringify({ error: "Database not found" });
    }

    const result = await Bun.$`sqlite3 -json ${dbPath} "
      SELECT
        (SELECT COUNT(*) FROM sprints) AS sprint_count,
        (SELECT MAX(completed_at) FROM phase_runs) AS last_pulse_at,
        (SELECT COUNT(*) FROM dispatch_log) AS dispatch_count,
        (SELECT number FROM sprints ORDER BY id DESC LIMIT 1) AS active_sprint,
        (SELECT status FROM sprints ORDER BY id DESC LIMIT 1) AS active_sprint_status
    "`.text();

    const data = JSON.parse(result);
    // Compute silence duration
    if (data.last_pulse_at) {
      const now = new Date();
      const last = new Date(data.last_pulse_at);
      const silence = Math.floor((now - last) / 1000);
      data.silence_seconds = silence;
      const h = Math.floor(silence / 3600);
      const m = Math.floor((silence % 3600) / 60);
      data.silence_human = h > 0 ? `${h}h ${m}m` : `${m}m`;
    } else {
      data.silence_human = "no pulses recorded";
    }
    data.db_path = dbPath;
    return JSON.stringify(data, null, 2);
  },
});
```

**No `.sh` file needed.** SQL executed directly via `Bun.$` with array args. JSON parsing and silence computation in TypeScript.

---

### 3. `list_files.ts` — Pure TypeScript

```typescript
import { tool } from "@opencode-ai/plugin";
import { glob } from "fs";

export default tool({
  description: "List files and directories matching a glob pattern",
  args: {
    pattern: tool.schema.string().describe("Glob pattern, e.g. 'backlog/*.md'"),
    root: tool.schema.string().optional().default(".").describe("Root directory"),
    max_results: tool.schema.number().optional().default(200).describe("Maximum entries to return"),
  },
  async execute(args, context) {
    const root = args.root || ".";
    const cwd = process.cwd();
    process.chdir(root);
    const entries = Array.from(new Bun.Glob(args.pattern).scanSync());
    process.chdir(cwd);

    const files = entries.slice(0, args.max_results);
    return JSON.stringify({
      files,
      count: files.length,
      truncated: entries.length > args.max_results,
    });
  },
});
```

**No `.sh` file needed.** `Bun.Glob` directly supports glob pattern matching.

---

### 4. `file_tree.ts` — Pure TypeScript

```typescript
import { tool } from "@opencode-ai/plugin";
import fs from "fs";
import path from "path";

function walk(dir, depth, maxDepth, dirsOnly, pattern) {
  if (depth > maxDepth) return [];
  const entries = [];
  const items = fs.readdirSync(dir, { withFileTypes: true });
  for (const item of items) {
    const fullPath = path.join(dir, item.name);
    const relPath = path.relative(process.cwd(), fullPath);
    if (dirsOnly && !item.isDirectory()) continue;
    if (pattern && !item.name.includes(pattern.replace("*", ""))) continue;
    entries.push({ name: relPath, type: item.isDirectory() ? "dir" : "file" });
    if (item.isDirectory()) {
      entries.push(...walk(fullPath, depth + 1, maxDepth, dirsOnly, pattern));
    }
  }
  return entries;
}

export default tool({
  description: "Show the directory tree structure",
  args: {
    root: tool.schema.string().optional().default(".").describe("Root directory"),
    depth: tool.schema.number().optional().default(3).describe("Maximum depth"),
    dirs_only: tool.schema.boolean().optional().default(false).describe("Show directories only"),
    pattern: tool.schema.string().optional().describe("Filter by glob pattern"),
  },
  async execute(args, context) {
    const root = args.root || ".";
    const entries = walk(root, 0, args.depth, args.dirs_only, args.pattern);
    return JSON.stringify({ root, depth: args.depth, entries, count: entries.length });
  },
});
```

**No `.sh` file needed.** Pure Node.js `fs` operations. No external commands.

---

### 5. `compare_files.ts` — Pure TypeScript

```typescript
import { tool } from "@opencode-ai/plugin";
import fs from "fs";

export default tool({
  description: "Compare two files and return structural differences",
  args: {
    file_a: tool.schema.string().describe("First file path"),
    file_b: tool.schema.string().describe("Second file path"),
    context_lines: tool.schema.number().optional().default(3).describe("Lines of context"),
    mode: tool.schema.string().optional().default("unified").describe("Diff mode: unified, word, or summary"),
  },
  async execute(args, context) {
    if (!fs.existsSync(args.file_a)) return JSON.stringify({ error: `File not found: ${args.file_a}` });
    if (!fs.existsSync(args.file_b)) return JSON.stringify({ error: `File not found: ${args.file_b}` });

    const result = await Bun.$`diff -u ${args.file_a} ${args.file_b}`.text();
    // diff exits 0 if identical, non-zero if different
    if (result === "") {
      return JSON.stringify({ identical: true, hudks: 0, additions: 0, deletions: 0, summary: "Files are identical" });
    }

    const lines = result.split("\n");
    const hunks = lines.filter(l => l.startsWith("@@")).length;
    const additions = lines.filter(l => l.startsWith("+")).length - 1; // remove header
    const deletions = lines.filter(l => l.startsWith("-")).length - 1;
    return JSON.stringify({
      identical: false,
      hunks: Math.max(0, hunks),
      additions: Math.max(0, additions),
      deletions: Math.max(0, deletions),
      summary: `${Math.max(0, hunks)} hunk(s), ${Math.max(0, additions)} addition(s), ${Math.max(0, deletions)} deletion(s)`,
      diff: result,
    });
  },
});
```

**No `.sh` file needed.** `Bun.$ diff` with array args. Parsing and JSON in TypeScript.

---

### 6. `lint_code.ts` — Pure TypeScript

```typescript
import { tool } from "@opencode-ai/plugin";
import fs from "fs";

export default tool({
  description: "Run static analysis on a Python file without executing it",
  args: {
    file_path: tool.schema.string().describe("Path to the Python file to lint"),
  },
  async execute(args, context) {
    if (!fs.existsSync(args.file_path)) {
      return JSON.stringify({ error: `File not found: ${args.file_path}` });
    }

    // Try pyflakes first
    const hasPyflakes = (await Bun.$`which pyflakes`.quiet()).exitCode === 0;
    if (hasPyflakes) {
      const result = await Bun.$`pyflakes ${args.file_path}`.text();
      const exitCode = result.exitCode;
      if (exitCode === 0) {
        return JSON.stringify({ file: args.file_path, valid: true, issues: [] });
      }
      // Parse pyflakes output
      const issues = result.stdout.split("\n").filter(Boolean).map(line => {
        // file.py:42:5: F821 undefined name 'foo'
        const parts = line.split(":");
        const message = parts.slice(3).join(":").trim();
        const code = message.split(/\s+/)[0];
        return {
          line: parseInt(parts[1]) || 0,
          column: parseInt(parts[2]) || 0,
          code,
          message,
          severity: ["F821", "F822", "F823", "F831"].includes(code) ? "error" : "warning",
        };
      });
      return JSON.stringify({
        file: args.file_path,
        valid: false,
        issues,
        error_count: issues.filter(i => i.severity === "error").length,
        warning_count: issues.filter(i => i.severity === "warning").length,
      });
    }

    // Fallback: py_compile
    const compileResult = await Bun.$`python3 -c "
import ast, py_compile, json, sys
try:
    py_compile.compile('${args.file_path}', doraise=True)
    print(json.dumps({'file': '${args.file_path}', 'valid': True, 'issues': []}))
except py_compile.PyCompileError as e:
    print(json.dumps({'file': '${args.file_path}', 'valid': False, 'issues': [{'line': 0, 'code': 'E000', 'message': str(e), 'severity': 'error'}]}))
    sys.exit(1)
"`.text();
    return compileResult;
  },
});
```

**No `.sh` file needed.** `pyflakes` called via `Bun.$` with array args. Output parsed in TypeScript.

---

### 7. `archive_features.ts` — Pure TypeScript

```typescript
import { tool } from "@opencode-ai/plugin";
import fs from "fs";
import path from "path";

export default tool({
  description: "Archive completed feature files from backlog/ to backlog/archive/{sprint}/",
  args: {
    sprintNum: tool.schema.string().describe("Sprint number (e.g., 001)"),
  },
  async execute(args, context) {
    const sprintNum = String(args.sprintNum).padStart(2, "0");
    const featuresDir = path.join("sprint", sprintNum, "features");
    const backlogDir = "backlog";
    const archiveDir = path.join("backlog", "archive", sprintNum);

    if (!fs.existsSync(featuresDir)) {
      return `No features directory found at ${featuresDir} — nothing to archive.`;
    }

    fs.mkdirSync(archiveDir, { recursive: true });
    let archived = 0;
    let notFound = 0;

    const featureFiles = fs.readdirSync(featuresDir).filter(f => f.startsWith("ft-") && f.endsWith(".md"));
    for (const fname of featureFiles) {
      const src = path.join(backlogDir, fname);
      if (fs.existsSync(src)) {
        fs.renameSync(src, path.join(archiveDir, fname));
        archived++;
      } else {
        notFound++;
      }
    }

    return `\n  Archive complete: ${archived} feature(s) archived, ${notFound} not found in backlog.`;
  },
});
```

**No `.sh` file needed.** Pure `fs` operations.

---

## Files to Delete

After all `.ts` files are rewritten, delete these `.sh` files:

- `scripts/search_files.sh`
- `scripts/read_pulse.sh`
- `scripts/list_files.sh`
- `scripts/file_tree.sh`
- `scripts/compare_files.sh`
- `scripts/lint_code.sh`
- `scripts/archive_features.sh`

These shell scripts are no longer referenced by any tool.

---

## Verification

```bash
# Each tool should return valid JSON without errors
search_files pattern:"import" max_results:3
list_files pattern:"backlog/*.md"
file_tree depth:2
compare_files file_a:README.md file_b:README.md
lint_code file_path:cli.py
read_pulse db_path:matsya.db
archive_features sprintNum:"07"
```

---

## Files to Change

| File | Action |
|------|--------|
| `.opencode/tools/search_files.ts` | Rewrite — inline logic, remove shell call |
| `.opencode/tools/read_pulse.ts` | Rewrite — inline logic, remove shell call |
| `.opencode/tools/list_files.ts` | Rewrite — inline logic using `Bun.Glob`, remove shell call |
| `.opencode/tools/file_tree.ts` | Rewrite — pure `fs` recursion, remove shell call |
| `.opencode/tools/compare_files.ts` | Rewrite — `Bun.$ diff` with array args, remove shell call |
| `.opencode/tools/lint_code.ts` | Rewrite — `Bun.$ pyflakes` with array args, remove shell call |
| `.opencode/tools/archive_features.ts` | Rewrite — pure `fs` operations, remove shell call |
| `scripts/search_files.sh` | **Delete** |
| `scripts/read_pulse.sh` | **Delete** |
| `scripts/list_files.sh` | **Delete** |
| `scripts/file_tree.sh` | **Delete** |
| `scripts/compare_files.sh` | **Delete** |
| `scripts/lint_code.sh` | **Delete** |
| `scripts/archive_features.sh` | **Delete** |

---

*Written by Saraswati, after tracing every tool failure to a shell quoting bug. Built by Matsya. No shell scripts this time.*
