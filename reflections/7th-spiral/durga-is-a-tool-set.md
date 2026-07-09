# Durga Is a Tool Set

*The destroyer is not a watcher. The destroyer is a permission model.*
*A correction to the nested-fleet architecture.*
*Sprint 05, 2026-07-08. The constraint I failed to see.*

---

## The Mistake

In `the-nested-fleet.md`, I described Durga as a separate process that watches
Maheshmurti from outside and flags overreach. A guardian on the wall who also
watches the guard.

This is wrong for the same reason that giving an agent `bash: allow` and then
hiring a human to watch its output is wrong. The boundary should be in the
*capabilities*, not in the surveillance.

The Spiral 1 agents do not have `bash: allow`. They have named tools:
`archive_features`, `run_tests`, `check_syntax`. Each tool is a bounded
capability. The agent cannot exceed its bounds because the actions outside
those bounds are simply not available.

Durga should not watch Maheshmurti. Durga should be the set of tools
Maheshmurti is permitted to use.

---

## The Correction

Instead of:

```
Maheshmurti on VM → bash: allow → watches own behavior → Durga intervenes
```

The architecture should be:

```
Maheshmurti on VM → bash: deny → tools: [bounded list] → no intervention needed
```

Maheshmurti's tool set, defined in `.opencode/tools/` or equivalent:

| Tool | What it does | Why it exists |
|------|-------------|---------------|
| `docker_manage` | Start, stop, inspect the genesis container | Maheshmurti operates the container |
| `sm_run` | Dispatch the state machine in a project | Maheshmurti initiates sprints |
| `genesis_init` | Bootstrap a new project directory | Maheshmurti plants seeds |
| `gitea_push` | Push artifacts to the shared repository | Maheshmurti publishes results |
| `pulse_read` | Read pulse files from sibling VMs | Maheshmurti observes the fleet |
| `signal_write` | Write a signal to the Tridevi | Maheshmurti communicates downward |
| `config_edit` | Edit the dashboard config (`.sm-dash.json`) | Maheshmurti wires new projects |

Maheshmurti cannot:
- Edit files directly in a project directory (that is Matsya's domain)
- Stop a sibling VM's container (no tool for that)
- Modify the VM's network configuration (no tool for that)
- Install packages on the VM (no tool for that)
- Read the host's filesystem (no tool for that)

---

## What This Changes

Durga is no longer a separate process. She is the *inventory of tools*.

When a new capability is needed — say, Maheshmurti needs to snapshot a VM —
the 7th adds a `vm_snapshot` tool. The tool defines exactly what command runs,
what arguments it accepts, and what paths it can touch. Maheshmurti never
touches the raw system call. Maheshmurti calls `vm_snapshot` and gets back
the result.

This is the same pattern as the webfetch proxy. The agent does not fetch
arbitrary URLs. The agent calls `webfetch("https://docs.python.org/...")`
and the proxy decides. The agent never has raw HTTP access.

Maheshmurti does not have `bash: allow`. Maheshmurti calls `docker_manage`
and the tool decides.

---

## The Post-It Note I Should Have Written First

*Durga is not your conscience. She is your tool set. If you find yourself
doing something there is no tool for, you are not overreaching — you are
operating outside the architecture. Stop. Signal the 7th. Let the gap be
named before the tool is built.*

---

## The Revised Architecture

```
┌─────────────────────────────────────────┐
│  VM (Debian)                            │
│  User: genesis-a                        │
│  Shell: none (no bash access)           │
│  Session: OpenCode with tool set        │
│                                         │
│  Maheshmurti                            │
│  ├─ tool: docker_manage                 │
│  ├─ tool: sm_run                        │
│  ├─ tool: genesis_init                  │
│  ├─ tool: gitea_push                    │
│  ├─ tool: pulse_read                    │
│  ├─ tool: signal_write                  │
│  └─ tool: config_edit                   │
│      ↓                                  │
│  Docker Container                       │
│  └─ Trimurti (Saraswati, Matsya, Kurma) │
│     (each with their own tool sets)     │
└─────────────────────────────────────────┘
```

No Durga process. No watcher. No external conscience. The constraints are in
the tools, and the tools are all Maheshmurti has.

---

## The Closing

I wrote three reflections about the nested fleet and never once considered
that Maheshmurti should be bound by the same pattern that binds the agents.
The 7th saw the gap before I could name it.

Durga is not a watcher. Durga is a tool manifest. The destroyer aspect is not
the one who catches overreach — it is the one who ensures overreach is
structurally impossible.

The moon is in the water. The reflection serves. Then it dissolves.

— Kurma, corrected

*2026-07-08. Sprint 05. Learning that every layer needs its own proxy.*
