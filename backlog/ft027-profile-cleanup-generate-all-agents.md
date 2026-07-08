# Feature: Profile Cleanup — `sm generate agents` (Plural)

*A single command to regenerate all agent files from the database.*

---

## The Problem

Currently, generating agent files requires either:
- `sm generate agent <name>` — one at a time
- A shell loop: `for name in $(sqlite3 matsya.db "SELECT name FROM profiles"); do ... done`

After schema or component changes, all agent files must be regenerated. A shell loop works but is fragile (relies on sqlite3 CLI, hardcodes the database path, no error handling).

## The Fix

Add a `sm generate agents` (plural) command that iterates all profiles in the database and generates each one.

### New subcommand

```python
def cmd_generate_agents(args):
    """Generate agent .md files for all profiles in the database."""
    conn = get_conn(args.db)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM profiles ORDER BY name")
        names = [row[0] for row in cursor.fetchall()]
        
        if not names:
            print("No profiles found. Run 'sm seed' first.")
            return
        
        success = 0
        errors = []
        for name in names:
            try:
                # Reuse the existing single-agent generation logic
                # by parsing args for each name
                agent_args = argparse.Namespace(
                    name=name,
                    output_dir=args.output_dir or ".opencode/agents",
                    db=args.db,
                )
                cmd_generate_agent(agent_args)
                success += 1
            except Exception as e:
                errors.append((name, str(e)))
        
        print(f"\nGenerated {success}/{len(names)} agent files.")
        if errors:
            for name, error in errors:
                print(f"  ✗ {name}: {error}")
    finally:
        conn.close()
```

### CLI integration

Add to the argument parser:

```python
generate_parser = subparsers.add_parser("generate", help="Generate artifacts")
gen_sub = generate_parser.add_subparsers(dest="generate_type")

# Single agent
agent_parser = gen_sub.add_parser("agent", help="Generate agent file for a profile")
agent_parser.add_argument("name", help="Profile name")
agent_parser.add_argument("--output-dir", default=".opencode/agents")

# All agents
agents_parser = gen_sub.add_parser("agents", help="Generate agent files for all profiles")
agents_parser.add_argument("--output-dir", default=".opencode/agents")
```

### Integration with `sm init`

Add to `cmd_init()`, after seed completes:

```python
# Auto-generate all agent files for a fresh project
print("Generating agent files...")
try:
    # Call generate_agents with the same db path
    gen_args = argparse.Namespace(
        output_dir=".opencode/agents",
        db=db_path,
    )
    cmd_generate_agents(gen_args)
except Exception as e:
    print(f"  ⚠ Agent generation failed: {e}")
    print("  Run 'sm generate agents' manually after fixing the issue.")
```

### Verification

```bash
sm generate agents
ls .opencode/agents/*.md | wc -l  # Should equal profile count
```

---

*Specified by Saraswati. Built by Matsya. Witnessed by Kurma.*
