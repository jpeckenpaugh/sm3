#!/usr/bin/env python3
"""
Matsya: Command-line interface for the state machine system.

Usage:
    sm seed                    Populate database from seed files
    sm run --profile <name>    Load profile and start state machine loop
    sm list profiles           Display all profiles
    sm list components         Display all components
    sm status                  Show current system state
    sm generate agent <name>   Render a profile as an OpenCode agent file

Python standard library only — no external dependencies.
"""

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path


# ─── Database helpers ───────────────────────────────────────────────────────

DEFAULT_DB = "matsya.db"


def get_db_path(db_arg=None):
    """Resolve database path, checking MATSYA_DB env var override."""
    if db_arg:
        return db_arg
    env_db = os.environ.get("MATSYA_DB")
    if env_db:
        return env_db
    return DEFAULT_DB


def get_conn(db_arg=None):
    """Get a SQLite connection."""
    db_path = get_db_path(db_arg)
    return sqlite3.connect(db_path)


def profile_exists(conn, name):
    """Return True if a profile with the given name exists."""
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM profiles WHERE name = ?", (name,))
    return cursor.fetchone() is not None


# ─── Command: seed ──────────────────────────────────────────────────────────

def cmd_seed(args):
    """Run the seed data loader."""
    # Import seed module and delegate
    import seed
    exit_code = seed.seed_database(
        db_path=args.db,
        schema_path=args.schema,
        seed_root=args.seed_root,
    )
    sys.exit(exit_code)


# ─── Command: run ───────────────────────────────────────────────────────────

def cmd_run(args):
    """Load a profile and start the state machine loop."""
    conn = get_conn(args.db)
    try:
        cursor = conn.cursor()

        # 1. Load profile
        cursor.execute(
            "SELECT name, version, header, permissions FROM profiles WHERE name = ?",
            (args.profile,),
        )
        row = cursor.fetchone()
        if row is None:
            print(f"✗ Profile '{args.profile}' not found in database.")
            print("  Run 'sm seed' first, or check the profile name.")
            sys.exit(1)

        profile_name, version, header_json, permissions_json = row
        header = json.loads(header_json)
        permissions = json.loads(permissions_json)

        # 2. Assemble components
        cursor.execute(
            """SELECT c.type, c.name, c.content, pc.order_idx, pc.params
               FROM profile_components pc
               JOIN components c ON pc.component_id = c.id
               JOIN profiles p ON pc.profile_id = p.id
               WHERE p.name = ?
               ORDER BY pc.order_idx""",
            (args.profile,),
        )
        components = cursor.fetchall()

        # 3. Build assembled body text
        body_parts = []
        for comp_type, comp_name, content, order_idx, params_json in components:
            if content:
                body_parts.append(content)
        assembled_body = "\n\n".join(body_parts)

        # 4. Construct config for state machine
        # Start with config.json (if it exists) as base, then CLI args override
        cfg = {}
        config_path = args.config or "config.json"
        if os.path.exists(config_path):
            with open(config_path) as f:
                file_cfg = json.load(f)
            cfg.update(file_cfg)

        # CLI args override config.json
        if args.max_iterations is not None:
            cfg["max_iterations"] = args.max_iterations
        if args.max_retries is not None:
            cfg["max_retries"] = args.max_retries

        # Add profile data (never overridden by config.json)
        cfg["profile"] = {
            "name": profile_name,
            "version": version,
            "header": header,
            "permissions": permissions,
            "assembled_body": assembled_body,
        }

        # Set environment variables for phase scripts to consume
        os.environ["MATSYA_PROFILE"] = profile_name
        os.environ["MATSYA_HEADER"] = header_json
        os.environ["MATSYA_PERMISSIONS"] = permissions_json
        os.environ["MATSYA_BODY"] = assembled_body

        print(f"  Profile: {profile_name} v{version}")
        print(f"  Role:    {header.get('role', 'unknown')}")
        print(f"  Mode:    {header.get('mode', 'all')}")
        print(f"  Temp:    {header.get('temperature', 'N/A')}")
        print(f"  Components: {len(components)} assembled")
        print()

        # 5. Import and run state machine
        from state_machine import run_with_config
        run_with_config(cfg)

    finally:
        conn.close()


# ─── Command: list ──────────────────────────────────────────────────────────

def cmd_list_profiles(args):
    """Display all profiles from the database."""
    conn = get_conn(args.db)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, version, header, permissions FROM profiles ORDER BY name"
        )
        rows = cursor.fetchall()

        if not rows:
            print("No profiles found. Run 'sm seed' first.")
            return

        if args.json:
            # JSON output
            output = []
            for name, version, header_json, permissions_json in rows:
                entry = {
                    "name": name,
                    "version": version,
                    "header": json.loads(header_json),
                    "permissions": json.loads(permissions_json),
                }
                output.append(entry)
            print(json.dumps(output, indent=2))
            return

        # Table output
        if args.verbose:
            # Show more detail
            headers = ("Name", "Version", "Role", "Mode", "Temperature", "Permissions")
            col_widths = [20, 10, 25, 8, 13, 40]
            fmt = "  ".join("{{:<{}}}".format(w) for w in col_widths)
            print(fmt.format(*headers))
            print("  ".join("─" * w for w in col_widths))
            for name, version, header_json, permissions_json in rows:
                header = json.loads(header_json)
                perms = json.loads(permissions_json)
                perms_str = json.dumps(perms, separators=(",", ":"))
                print(fmt.format(
                    name,
                    version,
                    header.get("role", ""),
                    header.get("mode", ""),
                    str(header.get("temperature", "")),
                    perms_str,
                ))
        else:
            # Compact view
            headers = ("Name", "Version", "Role", "Mode", "Temperature")
            col_widths = [20, 10, 25, 8, 13]
            fmt = "  ".join("{{:<{}}}".format(w) for w in col_widths)
            print(fmt.format(*headers))
            print("  ".join("─" * w for w in col_widths))
            for name, version, header_json, permissions_json in rows:
                header = json.loads(header_json)
                print(fmt.format(
                    name,
                    version,
                    header.get("role", ""),
                    header.get("mode", ""),
                    str(header.get("temperature", "")),
                ))
    finally:
        conn.close()


def cmd_list_components(args):
    """Display all components from the database."""
    conn = get_conn(args.db)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT type, name, content FROM components ORDER BY type, name"
        )
        rows = cursor.fetchall()

        if not rows:
            print("No components found. Run 'sm seed' first.")
            return

        if args.json:
            output = []
            for comp_type, name, content in rows:
                entry = {"type": comp_type, "name": name, "content": content}
                output.append(entry)
            print(json.dumps(output, indent=2))
            return

        # Table output
        truncate_at = args.truncate or 60
        headers = ("Type", "Name", "Content Preview")
        col_widths = [10, 28, truncate_at + 3]
        fmt = "  ".join("{{:<{}}}".format(w) for w in col_widths)
        print(fmt.format(*headers))
        print("  ".join("─" * w for w in col_widths))

        for comp_type, name, content in rows:
            if args.verbose:
                preview = content
            else:
                preview = (content[:truncate_at] + "...") if len(content) > truncate_at else content
            print(fmt.format(comp_type, name, preview))
    finally:
        conn.close()


# ─── Command: status ────────────────────────────────────────────────────────

def cmd_status(args):
    """Show current system state."""
    print("Matsya State Machine — Status")
    print("─" * 35)

    # 1. Check database existence and content
    db_path = get_db_path(args.db)
    if os.path.exists(db_path):
        conn = get_conn(args.db)
        try:
            cursor = conn.cursor()
            # Check if profiles table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='profiles'"
            )
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM profiles")
                profile_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM components")
                component_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM profile_components")
                pc_count = cursor.fetchone()[0]
                print(f"  Database:     {db_path} (ready)")
                print(f"  Profiles:     {profile_count}")
                print(f"  Components:   {component_count}")
                print(f"  Assemblies:   {pc_count}")
            else:
                print(f"  Database:     {db_path} (no schema — run 'sm seed')")
        finally:
            conn.close()
    else:
        print(f"  Database:     {db_path} (not found — run 'sm seed')")

    # 2. Check backlog
    backlog_path = args.backlog or "backlog"
    if os.path.isdir(backlog_path):
        backlog_files = [f for f in os.listdir(backlog_path) if f.endswith(".md")]
        print(f"  Backlog:      {len(backlog_files)} items")
    elif os.path.isfile(args.backlog or "backlog.txt"):
        # Also check backlog.txt format
        with open(args.backlog or "backlog.txt") as f:
            content = f.read().strip()
        lines = content.split("\n") if content else []
        print(f"  Backlog:      {len(lines)} items (backlog.txt)")
    else:
        print(f"  Backlog:      (not found)")

    # 3. Check signal file
    signal_path = args.signal or "vasuki.signal"
    if os.path.exists(signal_path):
        print(f"  Signal:       present")
    else:
        print(f"  Signal:       absent")

    # 4. Check iteration state file
    state_path = args.state or "matsya_state.json"
    if os.path.exists(state_path):
        with open(state_path) as f:
            state = json.load(f)
        print(f"  Iteration:    {state.get('iteration', '?')} of {state.get('max_iterations', '?')}")
        print(f"  Phase:        {state.get('phase', '?')}")
    else:
        print(f"  State:        Never run — run 'sm run --profile <name>' to begin")

    # 5. Show active profile if set
    active_profile = os.environ.get("MATSYA_PROFILE")
    if active_profile:
        print(f"  Active profile: {active_profile}")


# ─── Command: generate agent ────────────────────────────────────────────────

def cmd_generate_agent(args):
    """Render a profile as an OpenCode agent markdown file."""
    conn = get_conn(args.db)
    try:
        cursor = conn.cursor()

        # 1. Load profile
        cursor.execute(
            "SELECT name, version, header, permissions FROM profiles WHERE name = ?",
            (args.name,),
        )
        row = cursor.fetchone()
        if row is None:
            print(f"✗ Profile '{args.name}' not found in database.")
            print("  Run 'sm seed' first, or check the profile name.")
            sys.exit(1)

        profile_name, version, header_json, permissions_json = row
        header = json.loads(header_json)
        permissions = json.loads(permissions_json)

        # 2. Assemble components in order
        cursor.execute(
            """SELECT c.content
               FROM profile_components pc
               JOIN components c ON pc.component_id = c.id
               JOIN profiles p ON pc.profile_id = p.id
               WHERE p.name = ?
               ORDER BY pc.order_idx""",
            (args.name,),
        )
        component_rows = cursor.fetchall()
        body_parts = [row[0] for row in component_rows if row[0]]
        assembled_body = "\n\n".join(body_parts)

        # 3. Build agent markdown
        description = header.get("role", args.name)
        mode = header.get("mode", "all")
        temperature = header.get("temperature", 0.1)

        # Build permission YAML manually (no PyYAML dependency)
        permission_yaml = _permissions_to_yaml(permissions, indent=0)

        agent_md = f"""---
description: {description}
mode: {mode}
temperature: {temperature}
permission:
{permission_yaml}---

{assembled_body}
"""

        # 4. Determine output path
        agents_dir = args.output_dir or ".opencode/agents"
        os.makedirs(agents_dir, exist_ok=True)
        output_path = os.path.join(agents_dir, f"{args.name}.md")

        with open(output_path, "w") as f:
            f.write(agent_md)

        print(f"✓ Generated agent file: {output_path}")
        print(f"  Profile: {profile_name} v{version}")
        print(f"  Components: {len(component_rows)} assembled")

    finally:
        conn.close()


def _permissions_to_yaml(perms, indent=0):
    """Convert a permissions dict to YAML-like string without PyYAML.

    Produces properly indented YAML for the permission block.
    Keys containing special YAML characters (like '*') are quoted.
    """
    lines = []
    prefix = "  " * (indent + 1)

    def needs_quoting(s):
        """Check if a YAML key needs quoting (contains special chars)."""
        special = {"*", "?", "&", "!", "|", ">", "[", "]", "{", "}", "%"}
        return any(c in special for c in s) or ":" in s or "#" in s

    if isinstance(perms, dict):
        for key, value in perms.items():
            yaml_key = json.dumps(key) if needs_quoting(key) else key
            if isinstance(value, dict):
                lines.append(f"{prefix}{yaml_key}:")
                lines.append(_permissions_to_yaml(value, indent=indent + 1))
            elif isinstance(value, str):
                lines.append(f"{prefix}{yaml_key}: {value}")
            else:
                lines.append(f"{prefix}{yaml_key}: {json.dumps(value)}")
    elif isinstance(perms, str):
        lines.append(f"{prefix}{perms}")

    return "\n".join(lines)


# ─── Argument parser ────────────────────────────────────────────────────────

def build_parser():
    """Build the argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="sm",
        description="Matsya: State machine CLI",
    )
    parser.add_argument("--db", default=None, help="SQLite database path")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # seed
    p_seed = subparsers.add_parser("seed", help="Populate database from seed files")
    p_seed.add_argument("--schema", default="schema.sql", help="Schema SQL file path")
    p_seed.add_argument("--seed-root", default=".", help="Root directory containing seed data")
    p_seed.set_defaults(func=cmd_seed)

    # run
    p_run = subparsers.add_parser("run", help="Load a profile and start the state machine loop")
    p_run.add_argument("--profile", required=True, help="Profile name to load")
    p_run.add_argument("--config", default=None, help="Config JSON file path")
    p_run.add_argument("--max-iterations", type=int, default=None, help="Override max iterations")
    p_run.add_argument("--max-retries", type=int, default=None, help="Override max retries")
    p_run.set_defaults(func=cmd_run)

    # list
    p_list = subparsers.add_parser("list", help="List items from the database")
    p_list_sub = p_list.add_subparsers(dest="list_target", help="What to list")

    p_list_profiles = p_list_sub.add_parser("profiles", help="Display all profiles")
    p_list_profiles.add_argument("--verbose", "-v", action="store_true", help="Show permissions")
    p_list_profiles.add_argument("--json", action="store_true", help="Output as JSON")
    p_list_profiles.set_defaults(func=cmd_list_profiles)

    p_list_components = p_list_sub.add_parser("components", help="Display all components")
    p_list_components.add_argument("--verbose", "-v", action="store_true", help="Show full content")
    p_list_components.add_argument("--json", action="store_true", help="Output as JSON")
    p_list_components.add_argument("--truncate", type=int, default=60, help="Content preview length")
    p_list_components.set_defaults(func=cmd_list_components)

    # status
    p_status = subparsers.add_parser("status", help="Show current system state")
    p_status.add_argument("--backlog", default=None, help="Backlog directory or file path")
    p_status.add_argument("--signal", default=None, help="Signal file path")
    p_status.add_argument("--state", default=None, help="State file path")
    p_status.set_defaults(func=cmd_status)

    # generate
    p_gen = subparsers.add_parser("generate", help="Generate artifacts from profiles")
    p_gen_sub = p_gen.add_subparsers(dest="generate_target", help="What to generate")

    p_gen_agent = p_gen_sub.add_parser("agent", help="Generate an OpenCode agent file")
    p_gen_agent.add_argument("name", help="Profile name to render")
    p_gen_agent.add_argument("--output-dir", default=None, help="Output directory (default: .opencode/agents)")
    p_gen_agent.set_defaults(func=cmd_generate_agent)

    return parser


# ─── Entry point ────────────────────────────────────────────────────────────

def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    # Handle sub-subcommands for 'list' and 'generate'
    if args.command == "list" and args.list_target is None:
        # Show list subcommands
        parser.parse_args(["list", "--help"])
        sys.exit(1)

    if args.command == "generate" and args.generate_target is None:
        parser.parse_args(["generate", "--help"])
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
