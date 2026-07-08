# Tool: `archive_features.sh`

*A single-purpose bridge between the warden's watching and the filesystem it must occasionally touch.*

---

## The Problem

After a sprint completes, the backlog still contains all feature files. There is no signal distinguishing completed work from pending work. Over many sprints, the backlog accumulates indefinitely.

The warden-GATE decides whether the sprint is complete. That decision should produce a visible signal in the filesystem: completed features move out of `backlog/` into an archive.

## The Tool

A shell script at `scripts/archive_features.sh` that moves feature files from `backlog/` to `backlog/archive/{sprint_num}/`.

```bash
scripts/archive_features.sh <sprint_num>
```

### What it does

1. Reads `sprint/{sprint_num}/features/ft-*.md` — the features that were scoped into this sprint
2. For each file found there, checks if it also exists in `backlog/`
3. If it does, moves it to `backlog/archive/{sprint_num}/`
4. Reports count of archived and skipped files

### Example

```
$ bash scripts/archive_features.sh 001

  ✓ Archived: ft-01-project-setup.md
  ✓ Archived: ft-02-database-connection.md
  ✓ Archived: ft-03-schema-discovery.md

  Archive complete: 3 feature(s) archived, 0 not found in backlog.
```

### Resulting filesystem state

```
before:                              after:
backlog/                             backlog/
  ft-01-project-setup.md               archive/
  ft-02-database-connection.md           001/
  ft-03-schema-discovery.md               ft-01-project-setup.md
  ft-04-list-endpoints.md                 ft-02-database-connection.md
  ...                                    ft-03-schema-discovery.md
                                      ft-04-list-endpoints.md
                                      ...
```

The backlog shrinks. The archive grows. The signal is visible in `ls backlog/`.

## The Tool Definition (OpenCode Custom Tool)

The tool is defined as an OpenCode custom tool at `.opencode/tools/archive_features.ts`.
The tool definition file is TypeScript/JavaScript and registers the tool with the OpenCode
agent runtime. It may invoke a shell script or perform the file operations directly.

### Location

```
.opencode/tools/archive_features.ts
```

The filename becomes the tool name. This creates a tool called `archive_features`.

### Dependencies

The tool definition requires the `@opencode-ai/plugin` package and can use `Bun.$`
for shell execution (available natively in the OpenCode runtime).

### Tool signature

```typescript
import { tool } from "@opencode-ai/plugin";
import path from "path";

export default tool({
  description: "Archive completed feature files from backlog/ to backlog/archive/{sprint}/",
  args: {
    sprintNum: tool.schema.string().describe("Sprint number (e.g., 001)"),
  },
  async execute(args, context) {
    const scriptPath = path.join(
      context.directory,
      "scripts",
      "archive_features.sh"
    );
    const result = await Bun.$`bash ${scriptPath} ${args.sprintNum}`.text();
    return result.trim();
  },
});
```

### Context

The `execute` function receives `context` with:
- `context.directory` — the session working directory (project root)
- `context.worktree` — the git worktree root
- `context.agent` — the agent name
- `context.sessionID` — the current session ID

Use `context.directory` to resolve the path to `scripts/archive_features.sh`.

### How the agent invokes it

The warden-GATE agent calls the tool by name in its instructions.
The OpenCode runtime resolves `archive_features` to the tool definition in
`.opencode/tools/archive_features.ts` and executes it with the provided args.

### How agents access the tool

The tool is registered in `.opencode/tools/` and becomes available to any agent
that the OpenCode runtime dispatches to. The agent's profile does not need special
permissions — the tool itself is the permission boundary.

The warden-GATE profile declares the tool in its profile:

```json
{
  "tools": ["archive_features"]
}
```

This tells the OpenCode runtime that the warden-GATE agent is allowed to invoke
this specific tool. The agent cannot run arbitrary bash — it can only call
`archive_features`.

## Integration into the Pipeline

The tool is invoked at the end of SPRINT_GATE, after the gate passes but before
the next sprint begins. The warden's decision to proceed triggers the archive.

The SPRINT_GATE flow becomes:

1. warden-GATE agent evaluates backlog and review report
2. If backlog non-empty → exit 0 (continue)
3. **Agent calls `archive_features` tool with sprint number**
4. Tool moves completed feature files from `backlog/` to `backlog/archive/{n}/`
5. Sprint completes or loops

### Mode-specific component integration

```markdown
### On Sprint Complete

When the gate passes and the sprint is ready to continue:
- Call the `archive_features` tool with the current sprint number.
- This moves the sprint's features from `backlog/` to `backlog/archive/{n}/`.
- The backlog thus shrinks with each completed sprint, providing a visible
  signal of progress.
- You have access to the `archive_features` tool. Use it when your decision
  to proceed is made.
```

## Backward Compatibility

The tool is optional. If `.opencode/tools/archive_features.ts` does not exist,
the agent cannot call it and the sprint completes as before. No error, no crash.

---

*Specified by Saraswati. Implemented by Matsya. Used by warden-GATE. Watched by Kurma.*
