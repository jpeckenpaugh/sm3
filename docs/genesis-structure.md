# Genesis Directory Structure

The root workspace for all genesis-sm projects, repositories, and engine installations.

---

## Layout

```
/Users/jarad/genesis/
├── .sm-dash.json          # Dashboard config — lists all project databases
├── projects/              # sm init project directories
│   └── euchre/            # Example: EuchreGame sprint project
│       ├── euchre.db      # State machine database
│       ├── concept.md     # Seed concept
│       ├── .sm-config.json
│       ├── .opencode/agents/
│       ├── backlog/
│       ├── sprint/
│       └── <original source files>
├── repos/                 # Git repositories (shared with Gitea)
│   └── origin/            # Gitea user namespace
│       └── euchre.git     # Bare repo
└── engines/               # Versioned engine installations (future)
```

---

## Docker Compose

File: `/Users/jarad/git/sm1/docker-compose.yml`

### gen-v4 service

Mounts genesis and the sm3 engine code:

```yaml
gen-v4:
  volumes:
    - /Users/jarad/git/sm3:/root/sm           # Engine code + tools
    - /Users/jarad/genesis:/genesis            # Projects + config
    - ./configs:/configs:ro
```

### gitea service

Mounts the shared repos directory and configures Gitea to use it:

```yaml
gitea:
  image: gitea/gitea:latest
  volumes:
    - ./gitea-data:/data                       # Gitea config + SQLite DB
    - /Users/jarad/genesis/repos:/genesis/repos # Shared repos
  environment:
    - GITEA__repository__ROOT=/genesis/repos
    - GITEA__server__ROOT_URL=http://localhost:3001
    - GITEA__server__DOMAIN=localhost
    - GITEA__server__HTTP_PORT=3000
    - GITEA__database__DB_TYPE=sqlite3
  ports:
    - "3001:3000"                              # Web UI
    - "2222:22"                                # SSH
```

---

## Startup Sequence

After `docker compose up -d`:

### 1. Dashboard

Starts inside gen-v4 using the venv:

```bash
docker exec gen-v4 bash -c '
  source /root/sm/.venv/bin/activate
  cp /genesis/.sm-dash.json /root/.sm-dash.json
  cd /root/sm/ui
  python3 -m uvicorn main:app --host 0.0.0.0 --port 8001 --log-level warning
'
```

Open: `http://localhost:8001`

### 2. Gitea

First-time setup: open `http://localhost:3001`, complete the install screen.

Default settings from environment variables:
- Database: SQLite3 at `/data/gitea/gitea.db`
- Repo root: `/genesis/repos/`
- Admin user: create during install (e.g. `origin`)

### 3. Dashboard Config

The file `/genesis/.sm-dash.json` lists every project database:

```json
{
  "databases": [
    {
      "name": "Euchre Sprint",
      "path": "/genesis/projects/euchre/euchre.db"
    }
  ]
}
```

---

## Creating a New Project

### 1. Bootstrap

```bash
docker exec -w /genesis/projects gen-v4 bash -c '
  source /root/sm/.venv/bin/activate
  sm init --seed-root /root/sm my-project.db
'
```

This creates `/genesis/projects/<name>/` with:
- State machine database
- Agent profiles
- Phase scripts
- Sprint scaffolding

### 2. Write a concept

```bash
cat > /genesis/projects/<name>/concept.md << 'EOF'
# Project Concept
...
EOF
```

### 3. Add to dashboard

Edit `/genesis/.sm-dash.json`:

```json
{
  "databases": [
    { "name": "Euchre Sprint", "path": "/genesis/projects/euchre/euchre.db" },
    { "name": "New Project", "path": "/genesis/projects/<name>/<name>.db" }
  ]
}
```

Restart the dashboard to pick up the new config.

### 4. Push to Gitea

```bash
# From the host (or gen-v4 if git is configured):
cd /genesis/projects/<name>
git remote add gitea http://<user>:<password>@localhost:3001/<user>/<name>.git
git push -u gitea main
```

---

## Running the State Machine

```bash
docker exec -w /genesis/projects/<name> gen-v4 bash -c '
  source /root/sm/.venv/bin/activate
  sm run --profile scribe-PLAN --max-iterations 1
'
```

The dashboard shows real-time pulse data. After the sprint completes, git commit the results and push to Gitea for native diff/PR review.

---

## Replicating on Another Machine

1. Clone sm3: `git clone git@github.com:jpeckenpaugh/sm3.git`
2. Clone sm1 (compose): `git clone git@github.com:jpeckenpaugh/sm1.git`
3. Create `/Users/jarad/genesis/` with subdirectories
4. Update docker-compose.yml with volume mounts (see above)
5. `docker compose up -d`
6. Install Gitea via web UI
7. Copy projects from original machine's `/genesis/projects/`
8. Copy `.sm-dash.json`
9. Start dashboard

---

## Git Safety

Repositories created on the host and mounted into the container will trigger git's "dubious ownership" check (UID mismatch between host and container). The dashboard's git module auto-fixes this on each request, but for CLI operations inside the container:

```bash
docker exec gen-v4 git config --global --add safe.directory /genesis/projects/euchre
```

Or for all genesis projects:

```bash
docker exec gen-v4 git config --global --add safe.directory /genesis/projects/*
```

---

## Container Restart Safety

Only files in mounted volumes survive container recreation:

| Path | Survives? | Contains |
|------|-----------|----------|
| `/root/sm/` | Yes | Engine code, tools, ui |
| `/genesis/` | Yes | Projects, repos, dash config |
| `/root/.sm-dash.json` | **No** | Copied from `/genesis/` on startup |
| Gitea `/data/` | Yes | Gitea config + DB (in `./gitea-data/`) |
| Gitea `/genesis/repos/` | Yes | Bare git repos (shared) |

After a container restart, run the dashboard startup command to copy the config and start the server.

---

*Documented by Mahadevi, Spiral 6, 2026-07-08.*
