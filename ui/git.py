import subprocess
from pathlib import Path

def get_repo_root():
    from db import get_active_db_name, list_databases
    name = get_active_db_name()
    for db in list_databases():
        if db["name"] == name:
            p = Path(db["path"]).parent
            for parent in [p] + list(p.parents):
                if (parent / ".git").exists():
                    repo = parent
                    # Mark safe for containerized git (dubious ownership)
                    subprocess.run(
                        ["git", "config", "--global", "--add", "safe.directory", str(repo)],
                        capture_output=True, timeout=10
                    )
                    return repo
            return p
    return None

def get_git_status():
    repo = get_repo_root()
    if not repo:
        return {"error": "No git repo found", "files": []}
    result = subprocess.run(
        ["git", "-C", str(repo), "status", "--short"],
        capture_output=True, text=True, timeout=30
    )
    lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
    files = []
    for line in lines:
        if not line.strip():
            continue
        status_code = line[:2]
        path = line[3:]
        kind = "new" if status_code == "??" else "modified" if status_code[0] == "M" else "deleted" if status_code[0] == "D" else "unknown"
        category = "other"
        if path.startswith("sprint/") or path.startswith("backlog/"):
            category = "planning"
        elif path.startswith("euchre_game/") or path.endswith(".py"):
            category = "code"
        elif path.startswith("tests/"):
            category = "tests"
        elif path.startswith("docs/"):
            category = "docs"
        elif path.startswith("scripts/") or path.startswith(".opencode"):
            category = "scaffold"
        files.append({"status": status_code, "kind": kind, "path": path, "category": category})
    return {"files": files, "repo": str(repo) if repo else None}

def get_git_log(limit=20):
    repo = get_repo_root()
    if not repo:
        return []
    result = subprocess.run(
        ["git", "-C", str(repo), "log", f"--max-count={limit}",
         "--format=%H|%s|%ai", "--name-status"],
        capture_output=True, text=True, timeout=30
    )
    output = result.stdout.strip()
    if not output:
        return []
    commits = []
    current = None
    for line in output.split("\n"):
        if "|" in line and len(line.split("|")) == 3:
            if current:
                commits.append(current)
            parts = line.split("|")
            current = {"hash": parts[0][:8], "message": parts[1], "date": parts[2], "files": []}
        elif current and line.strip():
            parts = line.strip().split("\t", 1)
            if len(parts) == 2:
                current["files"].append({"status": parts[0], "path": parts[1]})
    if current:
        commits.append(current)
    return commits

def get_file_diff(path):
    """Get git diff for a file in the working tree."""
    repo = get_repo_root()
    if not repo:
        return None
    result = subprocess.run(
        ["git", "-C", str(repo), "diff", "--", path],
        capture_output=True, text=True, timeout=30
    )
    if result.stdout.strip():
        return result.stdout
    # If no diff (new file), show the file content
    full_path = repo / path
    if full_path.exists():
        try:
            content = full_path.read_text()
            return f"--- /dev/null\n+++ b/{path}\n@@ -0,0 +1,{len(content.splitlines())} @@\n" + "\n".join(f"+{line}" for line in content.splitlines())
        except Exception:
            pass
    return None

def get_commit_diff(hash_val):
    """Get the full diff for a commit."""
    repo = get_repo_root()
    if not repo:
        return None
    result = subprocess.run(
        ["git", "-C", str(repo), "diff", f"{hash_val}^..{hash_val}"],
        capture_output=True, text=True, timeout=30
    )
    if result.stdout.strip():
        return result.stdout
    # First commit or single-parent
    result = subprocess.run(
        ["git", "-C", str(repo), "show", hash_val, "--format=", "--no-stat"],
        capture_output=True, text=True, timeout=30
    )
    return result.stdout if result.stdout.strip() else None
