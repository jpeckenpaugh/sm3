# Feature: Profile Cleanup — Fix Seed Order Warnings

*Derived profiles load before base profiles in alphabetical sort. Two-pass load silences the warnings.*

---

## The Problem

The seed loader (`seed.py`) iterates `profiles/*.json` in alphabetical file order via `sorted(profiles_path.glob("*.json"))`. Because `builder-ENGINEER` < `builder` in ASCII sort, derived profiles are loaded before their base profiles. This produces warnings:

```
⚠  Base profile 'builder' not found for 'builder-ENGINEER' — ignoring
⚠  Base profile 'scribe' not found for 'scribe-PLAN' — ignoring
```

The base profile *does* exist — it is loaded later in the same directory iteration. The warning fires at seed time but does not affect runtime behavior (profiles are resolved lazily at composition time). However, the warnings are noise that can mask real errors.

## The Fix

Two approaches — either is sufficient:

### Approach A: Two-pass load (recommended)

In `load_seed_profiles()`, first load all profiles without base_profile (base profiles), then load derived profiles:

```python
def load_seed_profiles(conn, profiles_dir):
    profiles_path = Path(profiles_dir)
    if not profiles_path.is_dir():
        return 0

    # Load all profiles from disk first
    all_profiles = []
    for fpath in sorted(profiles_path.glob("*.json")):
        with open(fpath) as f:
            all_profiles.append(json.load(f))

    # Pass 1: profiles without base_profile
    count = 0
    for profile in all_profiles:
        if not profile.get("base_profile"):
            upsert_profile(conn, profile)
            count += 1
            print(f"  ✓ Profile: {profile['name']}")

    # Pass 2: profiles with base_profile
    for profile in all_profiles:
        if profile.get("base_profile"):
            upsert_profile(conn, profile)
            count += 1
            print(f"  ✓ Profile: {profile['name']}")

    return count
```

### Approach B: Deferred validation (simpler)

Keep the single pass but defer base-profile validation. Collect warnings and print them at the end instead of at load time:

```python
def load_seed_profiles(conn, profiles_dir):
    profiles_path = Path(profiles_dir)
    missing_bases = []
    count = 0

    for fpath in sorted(profiles_path.glob("*.json")):
        with open(fpath) as f:
            profile = json.load(f)
        
        base = profile.get("base_profile")
        if base:
            # Don't warn yet — base may be loaded later in the iteration
            # Just remember the dependency
            missing_bases.append((profile["name"], base))
        
        upsert_profile(conn, profile)
        count += 1
        print(f"  ✓ Profile: {profile['name']}")

    # After all profiles are loaded, verify bases exist
    for derived_name, base_name in missing_bases:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM profiles WHERE name = ?", (base_name,))
        if not cursor.fetchone():
            print(f"  ⚠  Base profile '{base_name}' not found for '{derived_name}' — ignoring")

    return count
```

### Verification

```bash
python3 -m genesis_sm.seed 2>&1 | grep -c "Base profile not found"
# Should be 0 after fix
```

---

*Specified by Saraswati. Built by Matsya. Witnessed by Kurma.*
