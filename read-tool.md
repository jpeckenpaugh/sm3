# Read Tool — Specification

*As experienced in the current OpenCode agent session.*

---

## Purpose

Reads a file or directory from the local filesystem and returns its contents.

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `filePath` | string | yes | Absolute path to the file or directory |
| `offset` | integer | no | Line number to start reading from (1-indexed) |
| `limit` | integer | no | Maximum number of lines to return (default 2000) |

## Behavior

### Files
Returns content with each line prefixed by `<line_number>: <content>`.
Lines longer than 2000 characters are truncated.

### Directories
Lists entries one per line, with a trailing `/` for subdirectories.

### Images / PDFs
Can render them as attachments when applicable.

### Error
Returns an error if the path does not exist.

---

## Constraints

1. **Must read before editing** — The `edit` tool refuses to run unless the file has been read first in the same conversation. This prevents blind writes without seeing what is there.

2. **No glob/find** — There is no glob or find tool. The agent can only read paths it already knows. Discovering an unknown file requires guessing its path or reading the parent directory.

3. **No grep** — There is no pattern-search tool. To find specific content within a file, the agent must read the entire file (or a large window of it).

4. **Sequential addressing** — Multiple files can be read in parallel in a single call, but each call must specify an exact absolute path. Relative paths are not supported.

---

## Common Usage Patterns

### Scan a directory to discover files
```
read { "filePath": "/root/sm" }
```
Returns: list of files and subdirectories.

### Read a known file
```
read { "filePath": "/root/sm/schema.sql" }
```
Returns: file contents with line numbers.

### Read a section of a large file
```
read { "filePath": "/root/sm/state_machine.py", "offset": 100, "limit": 50 }
```
Returns: lines 100–149.

---

## Notes for Agent Implementations

- Always use absolute paths — the tool does not resolve relative paths.
- If you get "File not found," check for typos or read the parent directory to confirm the exact filename.
- The 2000-line default limit means large files may be truncated silently. Use `offset` to paginate through them.
- The `edit` tool will fail if you have not read the target file in the current session. This is by design — always read before you write.
