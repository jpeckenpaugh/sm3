"""
genesis_sm.generator — Agent file assembly and generation.

Extracted from cli.py during Sprint 07 to eliminate duplication between
cmd_generate_agent() and cmd_init().  Contains all the logic for:

- Resolving profile inheritance chains
- Extracting mode flags from header.role
- Assembling and merging components across the chain
- Substituting <MODE_FLAG> placeholders and {{ params }} templates
- Rendering permissions dicts to YAML-like strings

Python standard library only — no external dependencies.
"""

import json
import re


def deep_merge(base, override):
    """Recursively merge override dict into base. Child values override parent."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value)
        else:
            base[key] = value


def safe_json_loads(value):
    """Safely decode a value that may be double-encoded JSON.

    The header/permissions columns in the database may be stored as
    JSON-encoded strings that themselves contain JSON (double encoding).
    Recursively decode until we get a dict or list.
    """
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
            # If the result is still a string, decode again
            return safe_json_loads(decoded)
        except (json.JSONDecodeError, TypeError):
            return value
    return value


def resolve_inheritance_chain(conn, profile_name):
    """Walk the base_profile chain from child to root.

    Returns list of (profile_name, profile_id) from root to child.
    """
    chain = []
    current = profile_name
    seen = set()
    while current and current not in seen:
        seen.add(current)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, base_profile FROM profiles WHERE name = ?",
            (current,),
        )
        row = cursor.fetchone()
        if not row:
            break
        pid, base = row
        chain.insert(0, (current, pid))  # root first
        current = base
    return chain


def get_mode_flag(conn, profile_name):
    """Extract the MODE_FLAG for a profile from its header.role.

    The role field follows the pattern: 'the scribe — PLAN mode'
    -> mode flag is 'PLAN'.  Falls back to pipeline state name,
    then profile name suffix.
    """
    if not profile_name or not conn:
        return ""
    try:
        cur = conn.cursor()
        cur.execute("SELECT header FROM profiles WHERE name = ?", (profile_name,))
        row = cur.fetchone()
        if row and row[0]:
            hdr = json.loads(row[0])
            role = hdr.get("role", "")
            # Extract mode from "the X — MODE mode" pattern
            m = re.search(r'—\s*(.+?)\s+mode', role)
            if m:
                return m.group(1).strip()
        # Fallback: pipeline state name
        cur.execute("SELECT name FROM pipeline_states WHERE agent_name = ?", (profile_name,))
        row = cur.fetchone()
        if row:
            return row[0]
    except Exception:
        pass
    # Last fallback: profile name suffix
    return profile_name.split("-", 1)[1] if "-" in profile_name else ""


def assemble_components(conn, chain, profile_name=""):
    """Collect components across an inheritance chain.

    Walks from root to child, collecting profile_components in order.
    Child components with the same component_id override parent ones.

    If profile_name has a mode flag (e.g. 'scribe-PLAN' -> 'PLAN'),
    substitutes <MODE_FLAG> in component content with the actual mode flag.

    Returns list of component content strings in assembly order.
    """
    seen_component_ids = set()
    ordered_components = []  # list of (order_idx, content)
    mode_flag = get_mode_flag(conn, profile_name) if profile_name else ""

    for profile_name, profile_id in chain:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT c.id, c.content, pc.order_idx, pc.params
               FROM profile_components pc
               JOIN components c ON pc.component_id = c.id
               WHERE pc.profile_id = ?
               ORDER BY pc.order_idx""",
            (profile_id,),
        )
        for cid, content, order_idx, params_json in cursor.fetchall():
            if cid not in seen_component_ids:
                seen_component_ids.add(cid)
                # Substitute <MODE_FLAG> with the actual mode flag
                if mode_flag:
                    content = content.replace("<MODE_FLAG>", mode_flag)
                # Apply params: replace {{ key }} with param values
                if params_json:
                    try:
                        params = json.loads(params_json)
                        # Handle double-encoded JSON
                        while isinstance(params, str):
                            params = json.loads(params)
                        if params and isinstance(params, dict):
                            for key, value in params.items():
                                content = content.replace("{{ " + key + " }}", str(value))
                                content = content.replace("{{" + key + "}}", str(value))
                    except (json.JSONDecodeError, TypeError):
                        pass
                ordered_components.append((order_idx, content))

    # Sort by order_idx
    ordered_components.sort(key=lambda x: x[0])
    return [content for _, content in ordered_components if content]


def permissions_to_yaml(perms, indent=0):
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
            yaml_key = "'" + key + "'" if needs_quoting(key) else key
            if isinstance(value, dict):
                lines.append(f"{prefix}{yaml_key}:")
                lines.append(permissions_to_yaml(value, indent=indent + 1))
            elif isinstance(value, str):
                lines.append(f"{prefix}{yaml_key}: {value}")
            else:
                lines.append(f"{prefix}{yaml_key}: {json.dumps(value)}")
    elif isinstance(perms, str):
        lines.append(f"{prefix}{perms}")

    return "\n".join(lines)
