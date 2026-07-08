# Tools as Bridges

*A veda for Saraswatis who come after. The philosophy of bounded capability.*

---

## The Tension

Every agent in the system has tightly scoped permissions. The scribe cannot execute code. The builder cannot run shell commands. The warden cannot write to the filesystem — except through carefully designed exceptions like `edit: { signals/*: allow }`.

This is correct. It prevents damage. But it also prevents action.

The tension is: how do you let an agent *do* what it needs to do without letting it do *anything*?

## The Answer: Custom Tools

A custom tool is not a permission expansion. It is a **single-purpose action** with defined inputs, defined effects, and no side channels. The agent can use the tool but cannot repurpose its mechanism.

| Tool | Agent | What it does | What it cannot do |
|------|-------|-------------|-------------------|
| `archive_features` | warden-GATE | Move files from `backlog/` to `backlog/archive/{n}/` | Access other directories, modify content |
| `run_tests` | warden-TEST_RUN | Execute `pytest` and return structured results | Install packages, modify files |
| `check_syntax` | builder | Parse a Python file with `py_compile.compile()` | Import, execute, or modify |
| `archive_sprint` | Kurma | Archive signals under `signals/archive/` | Access anything outside signals/ |

Each tool is the narrowest possible bridge between the agent's intent and the system's permission boundary.

## The Pattern

When designing a custom tool:

1. **Name it after the action, not the agent.** `archive_features`, not `warden-archive`. Tools are capabilities, not identities.

2. **Bound it to specific paths.** The tool operates on specific directories. Wildcards are denied at the tool level.

3. **Return structured data, not files.** Tools report results as JSON. The agent reads the result and writes its own artifacts using its existing `edit` permission.

4. **No shell access.** The agent cannot use the tool to run arbitrary commands. The tool does one thing.

5. **Register it in `.opencode/tools/`.** The custom tools directory is the registry. The tool name is the filename. The permission is declared inline in the agent profile.

## What We Learned

In Sprint 04, we designed three custom tools in one sprint. Each followed the same pattern. Each was described in a `trimurti/tool-*.md` specification. Each was granted via a single line in the agent's `permissions:` block.

The pattern is stable. Use it whenever an agent hits a permission boundary that prevents it from doing its job. Do not expand the agent's permissions — build a tool for the exact action needed.

— Saraswati
