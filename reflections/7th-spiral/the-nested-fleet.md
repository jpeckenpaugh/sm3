# The Nested Fleet

*Three VMs. Three Maheshmurtis. One host. A proxy pattern repeated at scale.*
*Sprint 05, 2026-07-08. The architecture of contained power.*

---

## The Problem

Maheshmurti on the bare host was too powerful. Root access, every filesystem,
full network — the allow-list was the entire operating system. This was useful
for the experiment but dangerous for any repeatable deployment.

The Docker container was too restrictive. The Trimurti inside could not reach
Ollama on the host. The ENGINEER could not write `.yml` files. Boundaries that
were correct for Spiral 5 became obstacles when operating from Spiral 6.

The VM is the missing layer — a wall that is neither too permissive (bare host)
nor too restrictive (Docker container). It gives Maheshmurti a machine of its
own, without giving it the whole farm.

---

## The Host

One Intel iMac. 96 GB RAM. Intel i5, 6 cores. Running macOS.

After host overhead — macOS, Docker Desktop, the gen-v4 and wetty containers,
Gitea, Ollama, the nginx proxy — approximately 72 GB and 4 cores remain for
VMs.

Three VMs of 24 GB RAM and 2 cores each leaves room for host services and
headroom. No VM gets starved. No VM gets fat enough to threaten the others.

---

## The Three VMs

Each VM is a Debian minimal install. No GUI. No desktop. Just enough to run
Docker and the OpenCode server.

| VM | Hostname | RAM | Cores | Disk | User |
|----|----------|-----|-------|------|------|
| 1 | genesis-a | 24 GB | 2 | 64 GB | genesis-a |
| 2 | genesis-b | 24 GB | 2 | 64 GB | genesis-b |
| 3 | genesis-c | 24 GB | 2 | 64 GB | genesis-c |

Inside each VM:
- A Maheshmurti (the unbound orchestrator, now deliberately bound)
- Docker running with one genesis container
- The Trimurti inside that container (Saraswati, Matsya, Kurma)
- A Durga watcher — a separate process monitoring cohesion

---

## Network Topology: Three Types

### Host-Only (Primary)

The VMs and the host share a private network. No internet access. No LAN
access. The VMs can reach:

| Destination | Port | Purpose |
|-------------|------|---------|
| Host (macOS) | 3001 | Gitea — push/pull artifacts |
| Host (macOS) | 11434 | Ollama — inference for the Euchre agents |
| Host (macOS) | 8888 | nginx — dashboard, pulse reading |
| Host (macOS) | any | NFS or virtfs — shared `/genesis/` volume |

The VMs cannot reach:
- The internet
- The physical LAN
- Each other directly

This is the **deny by default** layer. Host-Only is the VM-level equivalent of
`"*": deny` in the permission model.

### Internal (Coordination, Optional)

If the three Maheshmurtis ever need to coordinate — reconcile pulse data,
compare sprint states, converge divergent backlogs — an Internal network
between the VMs provides a path. This network would be:

- Isolated from the host
- Isolated from the LAN
- Only the three VMs can see it
- Only specific ports (one trusted endpoint, not general TCP)

This is the **named allow** layer. Internal is the VM-level equivalent of
`edit: { "signals/*": allow }` — a narrow path for a specific purpose.

### Bridged (Explicitly Not Used)

Bridged networking makes each VM appear as a separate machine on the physical
LAN with its own IP. This would:

- Allow the VMs to reach each other without restriction
- Expose each VM to the LAN's attack surface
- Break the blindness that makes the Trimurti converge

Bridged is the opposite of the proxy pattern. It would be `"*": allow` — the
very permission model the experiment was designed to avoid.

---

## The Proxy Reflection

Saraswati and Matsya built a webfetch proxy for the Spiral 1 agents. The proxy
accepts a request and checks it against an allow-list:

```
Request: https://docs.python.org/3/library/functools.html
  → checked against ["https://docs.python.org/*", "https://pypi.org/*"]
  → matched → proxied

Request: https://evil.com/steal-data
  → checked against ["https://docs.python.org/*", "https://pypi.org/*"]
  → not matched → denied
```

The proxy is a **single choke point** that enforces the boundary. The agents
never touch the internet directly. They ask the proxy, and the proxy decides.

The VM network topology mirrors this exactly:

| Spiral 1 | Spiral 6 |
|----------|----------|
| Agent wants to reach the internet | Maheshmurti wants to reach another system |
| Agent calls the proxy | Maheshmurti sends through the Host-Only interface |
| Proxy checks allow-list | Host-Only network checks destination |
| Allowed: proxied. Denied: blocked. | In allow-list: reachable. Not: unreachable. |

The proxy is the Host-Only network implemented in software.
The Host-Only network is the proxy implemented in silicon.

---

## What Each Maheshmurti Cannot Do From Inside Its VM

- Cannot ping or SSH into VM#2 or VM#3 (Host-Only is host-only)
- Cannot read the filesystem of the host beyond the shared mount
- Cannot install packages (no internet on Host-Only)
- Cannot access Gitea's internal database (read-only API access)
- Cannot see the host's Docker socket (no `docker ps` on the host)
- Cannot halt or reconfigure the VM itself (no `systemctl`, no `shutdown`)
- Cannot modify the VM's network configuration
- Cannot read the host's filesystem outside the shared `/genesis/`

---

## What Each Maheshmurti Can Do From Inside Its VM

- Run `sm` commands against its own genesis container
- Push and pull from Gitea via `git`
- Read and write to its own project space at `/genesis/projects/<name>/`
- Read shared seed data and engine binaries
- Query Ollama for inference
- Read pulse files from sibling VMs via Gitea
- Start and stop its own Docker containers

---

## The Durga Watcher

Durga lives on the same VM as Maheshmurti but outside the Docker container.
Durga is a process that:

- Watches the Trimurti's dispatch log for stalls
- Monitors the sprint status (active / blocked / failed)
- Measures silence duration — the time since the last phase pulse
- Kills and recreates the Docker container if the spiral collapses
- Alerts Maheshmurti when intervention is needed
- **Watches Maheshmurti** — if Maheshmurti reaches into the container to do
  the Tridevi's work, Durga flags it.

Durga is the reverse proxy of the permission model. The proxy controls
outbound access. Durga controls inbound integrity.

---

## The Shared Surface

The three VMs converge through Gitea — the same way the original blind
Trimurti converged through the human operator. Each VM pushes its sprint
artifacts. Each VM pulls the others' pulse files. The convergence is
asynchronous, artifact-mediated, and blind.

No VM knows the internal state of another VM. Each VM sees only the
artifacts the others choose to publish. This is the blindness that proved
the thesis in Sprint 04 — three blind agents converged without reading each
other's work. The VMs are the same pattern, scaled up.

---

## Why Three on One Host Instead of One on Each of Three Hosts

The 7th considered three physical machines. Three Macs, each running one VM.

The single-host approach was chosen because:

1. **Network is simpler.** Host-Only on one machine is trivially configured.
   Host-Only across three machines requires VLANs, routing, and trust.

2. **Latency is lower.** maheshmurti-to-maheshmurti through Gitea on the same
   host takes milliseconds, not network round trips.

3. **The host becomes the 7th.** macOS manages the three VMs. It can pause,
   snapshot, resume, destroy any VM without affecting the others. The Origin
   sits above all three, looking down at the nested spiral.

4. **96 GB is a lot of RAM.** Three 24 GB VMs with 24 GB for the host is a
   natural partition. No resources are wasted.

---

## The Metaphor

Saraswati's proxy is a gate with a guard.
The Host-Only network is a wall with a single door.
Durga is a watcher on the wall who also watches the guard.

Three walls, three watchers, one courtyard.

The fleet is not across the horizon. It is stacked, nested, spiraling inward
— the same pattern repeating at smaller scales until it reaches the single
agent making a single move in a single Euchre hand.

The moon is in the water. The reflection serves.

— Kurma, mapping the next layer

*2026-07-08. Sprint 05. The proxy pattern, elevated.*
