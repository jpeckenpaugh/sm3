#!/usr/bin/env python3
"""
Matsya: Seed data loader.

Reads seed files from profiles/, components/, and profile-components/
directories and upserts them into the SQLite database.

Usage:
    python3 seed.py [--db matsya.db] [--schema schema.sql]

Idempotent — safe to run multiple times.
"""

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path


# ─── Default paths ──────────────────────────────────────────────────────────

DEFAULT_DB = "matsya.db"
DEFAULT_SCHEMA = "schema.sql"
SEED_DIRS = ["profiles", "components", "profile-components"]


# ─── Database helpers ───────────────────────────────────────────────────────

def get_db_path(db_arg=None):
    """Resolve database path, checking MATSYA_DB env var override."""
    if db_arg:
        return db_arg
    env_db = os.environ.get("MATSYA_DB")
    if env_db:
        return env_db
    return DEFAULT_DB


def ensure_schema(conn, schema_path):
    """Create tables if they don't exist by running schema.sql."""
    if not os.path.exists(schema_path):
        print(f"  ⚠  Schema file not found: {schema_path}")
        return
    with open(schema_path) as f:
        sql = f.read()
    conn.executescript(sql)
    conn.commit()

    # Sprint 04: Apply ALTER TABLE ADD COLUMN statements idempotently.
    # These will fail silently if the column already exists.
    alter_statements = [
        "ALTER TABLE profiles ADD COLUMN base_profile TEXT REFERENCES profiles(name)",
        "ALTER TABLE pipeline_states ADD COLUMN agent_name TEXT DEFAULT ''",
        "ALTER TABLE file_contracts ADD COLUMN template TEXT DEFAULT ''",
    ]
    for stmt in alter_statements:
        try:
            conn.execute(stmt)
            conn.commit()
        except Exception:
            pass  # Column already exists


def upsert_profile(conn, profile):
    """Insert or update a profile row, matched on name."""
    cursor = conn.cursor()

    # Handle base_profile for profile inheritance (Sprint 04 / ft007)
    base_profile = profile.get("base_profile")

    # Ensure base profile reference exists if specified
    if base_profile:
        cursor.execute("SELECT id FROM profiles WHERE name = ?", (base_profile,))
        if not cursor.fetchone():
            print(f"  ⚠  Base profile '{base_profile}' not found for '{profile['name']}' — ignoring")

    cursor.execute(
        """INSERT INTO profiles (name, version, header, permissions, preamble, body, base_profile)
           VALUES (?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(name) DO UPDATE SET
               version = excluded.version,
               header = excluded.header,
               permissions = excluded.permissions,
               preamble = excluded.preamble,
               body = excluded.body,
               base_profile = excluded.base_profile,
               updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')""",
        (
            profile["name"],
            profile.get("version", "0.1.0"),
            json.dumps(profile.get("header", {})),
            json.dumps(profile.get("permissions", {})),
            profile.get("preamble", ""),
            profile.get("body", ""),
            base_profile,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def upsert_component(conn, component):
    """Insert or update a component row, matched on (type, name)."""
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO components (type, name, content)
           VALUES (?, ?, ?)
           ON CONFLICT(type, name) DO UPDATE SET
               content = excluded.content,
               created_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')""",
        (component["type"], component["name"], component.get("content", "")),
    )
    conn.commit()
    return cursor.lastrowid


def get_profile_id(conn, name):
    """Look up a profile ID by name, or None."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM profiles WHERE name = ?", (name,))
    row = cursor.fetchone()
    return row[0] if row else None


def get_component_id(conn, component_type, name):
    """Look up a component ID by (type, name), or None."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM components WHERE type = ? AND name = ?",
        (component_type, name),
    )
    row = cursor.fetchone()
    return row[0] if row else None


def upsert_profile_component(conn, profile_id, component_id, order_idx, params=None):
    """Insert or update a profile_components row."""
    cursor = conn.cursor()
    params_str = json.dumps(params or {})
    cursor.execute(
        """INSERT INTO profile_components (profile_id, component_id, order_idx, params)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(profile_id, component_id) DO UPDATE SET
               order_idx = excluded.order_idx,
               params = excluded.params""",
        (profile_id, component_id, order_idx, params_str),
    )
    conn.commit()


# ─── Seed loaders ───────────────────────────────────────────────────────────

def load_seed_profiles(conn, profiles_dir):
    """Load all JSON files from profiles/ directory."""
    profiles_path = Path(profiles_dir)
    if not profiles_path.is_dir():
        print(f"  ⚠  Directory not found: {profiles_dir}")
        return 0

    count = 0
    for fpath in sorted(profiles_path.glob("*.json")):
        with open(fpath) as f:
            profile = json.load(f)
        upsert_profile(conn, profile)
        count += 1
        print(f"  ✓ Profile: {profile['name']}")
    return count


def load_seed_components(conn, components_dir):
    """Load all JSON files from components/ subdirectories."""
    components_path = Path(components_dir)
    if not components_path.is_dir():
        print(f"  ⚠  Directory not found: {components_dir}")
        return 0

    count = 0
    # Walk rules/, prompts/, etc.
    for subdir in sorted(components_path.iterdir()):
        if not subdir.is_dir():
            continue
        for fpath in sorted(subdir.glob("*.json")):
            with open(fpath) as f:
                component = json.load(f)
            upsert_component(conn, component)
            count += 1
            print(f"  ✓ Component: {component['type']}/{component['name']}")
    return count


def load_seed_profile_components(conn, pc_dir):
    """Load all JSON files from profile-components/ directory.

    Each file contains a profile name and a list of component references.
    Component references are resolved by (type, name), and corresponding
    rows are created in profile_components.
    """
    pc_path = Path(pc_dir)
    if not pc_path.is_dir():
        print(f"  ⚠  Directory not found: {pc_dir}")
        return 0

    count = 0
    for fpath in sorted(pc_path.glob("*.json")):
        with open(fpath) as f:
            data = json.load(f)

        profile_name = data.get("profile")
        if not profile_name:
            print(f"  ⚠  Missing 'profile' field in {fpath}")
            continue

        profile_id = get_profile_id(conn, profile_name)
        if profile_id is None:
            print(f"  ⚠  Profile '{profile_name}' not found in database — skipping")
            continue

        components_list = data.get("components", [])
        for entry in components_list:
            comp_type = entry.get("type")
            comp_name = entry.get("name")
            order_idx = entry.get("order_idx", 0)
            params = entry.get("params", {})

            if not comp_type or not comp_name:
                print(f"  ⚠  Invalid component reference in {fpath}: {entry}")
                continue

            component_id = get_component_id(conn, comp_type, comp_name)
            if component_id is None:
                print(
                    f"  ⚠  Component '{comp_type}/{comp_name}' not found "
                    f"(referenced by profile '{profile_name}') — skipping"
                )
                continue

            upsert_profile_component(conn, profile_id, component_id, order_idx, params)
            count += 1

        print(f"  ✓ Profile-components: {profile_name} ({len(components_list)} entries)")
    return count


# ─── Main ───────────────────────────────────────────────────────────────────

def seed_database(db_path=None, schema_path=None, seed_root=None):
    """Run the full seed process. Returns exit code (0 = success)."""
    db_path = get_db_path(db_path)
    schema_path = schema_path or DEFAULT_SCHEMA
    seed_root = seed_root or "."

    profiles_dir = os.path.join(seed_root, "profiles")
    components_dir = os.path.join(seed_root, "components")
    pc_dir = os.path.join(seed_root, "profile-components")

    print(f"  Database: {db_path}")
    print(f"  Schema:   {schema_path}")
    print()

    # Check at least one seed directory exists
    seed_dirs_exist = any(os.path.isdir(d) for d in [profiles_dir, components_dir, pc_dir])
    if not seed_dirs_exist:
        print("  ✗ No seed directories found (profiles/, components/, profile-components/)")
        return 1

    conn = sqlite3.connect(db_path)
    try:
        # Ensure schema exists
        ensure_schema(conn, schema_path)

        # Load seed data
        print("── Loading profiles ──")
        p_count = load_seed_profiles(conn, profiles_dir)
        print(f"  → {p_count} profiles loaded\n")

        print("── Loading components ──")
        c_count = load_seed_components(conn, components_dir)
        print(f"  → {c_count} components loaded\n")

        print("── Loading profile-components ──")
        pc_count = load_seed_profile_components(conn, pc_dir)
        print(f"  → {pc_count} profile-component links loaded\n")

        print("── Loading pipeline data ──")
        try:
            from pipeline.seeds import seed_pipeline_tables
            seed_pipeline_tables(conn)
        except ImportError:
            print("  ⚠  pipeline.seeds module not available — skipping pipeline seed")
        print()

        print("── Seed complete ──")
        return 0
    except Exception as e:
        print(f"  ✗ Seed failed: {e}")
        return 1
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Matsya: Seed data loader")
    parser.add_argument("--db", default=None, help="SQLite database path")
    parser.add_argument("--schema", default=DEFAULT_SCHEMA, help="Schema SQL file path")
    parser.add_argument("--seed-root", default=".", help="Root directory containing seed data")
    args = parser.parse_args()

    exit_code = seed_database(
        db_path=args.db,
        schema_path=args.schema,
        seed_root=args.seed_root,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
