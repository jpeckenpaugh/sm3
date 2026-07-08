# Feature: Profile Cleanup — Remove `body` and `preamble` Zombie Columns

*Dead columns confirmed by baseline. Remove the clutter._

---

## The Problem

The `profiles` table has two columns that are written but never read:

```sql
body     TEXT DEFAULT '',
preamble TEXT DEFAULT '',
```

- **`body`:** Written by `seed.py` line 80 from `profile.get("body", "")`. The on-disk profile JSONs haven't had a `body` field since component composition was introduced. All 16 profiles have `length(body) = 0`.
- **`preamble`:** Written by `seed.py` line 80 from `profile.get("preamble", "")`. The on-disk profile JSONs don't have a `preamble` field. All 16 profiles have `length(preamble) = 0`.

Neither column is read by `cmd_generate_agent()` (which uses component composition) nor by any pipeline code. They are zombies — written with empty data, never read, occupying schema space.

## The Fix

### 1. Schema migration

SQLite does not support `ALTER TABLE DROP COLUMN` natively (before 3.35.0). Use the recreate approach:

```sql
-- 1. Create new table without body/preamble
CREATE TABLE profiles_new (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    version     TEXT    NOT NULL DEFAULT '0.1.0',
    header      TEXT    DEFAULT '{}',
    permissions TEXT    DEFAULT '{}',
    base_profile TEXT   REFERENCES profiles(name),
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

-- 2. Copy data
INSERT INTO profiles_new (id, name, version, header, permissions, base_profile, created_at, updated_at)
SELECT id, name, version, header, permissions, base_profile, created_at, updated_at FROM profiles;

-- 3. Swap tables
DROP TABLE profiles;
ALTER TABLE profiles_new RENAME TO profiles;
```

### 2. Update `seed.py`

Remove `body` and `preamble` from the `INSERT INTO profiles` statement at line 80:

```python
# Before:
cursor.execute(
    """INSERT INTO profiles (name, version, header, permissions, preamble, body, base_profile)
       VALUES (?, ?, ?, ?, ?, ?, ?) ...""",
    (profile["name"], ..., profile.get("preamble", ""), profile.get("body", ""), base_profile),
)

# After:
cursor.execute(
    """INSERT INTO profiles (name, version, header, permissions, base_profile)
       VALUES (?, ?, ?, ?, ?) ...""",
    (profile["name"], ..., base_profile),
)
```

### 3. Update `schema.sql`

Remove the `body` and `preamble` column definitions from the CREATE TABLE statement.

### Backward compatibility

- This is a schema change. Existing databases need migration.
- The migration is safe: `body` and `preamble` are empty for all existing rows, and no code reads them.
- `schema.sql` should first attempt the new CREATE TABLE, then try the old one for backward compatibility (or detect schema version).

---

*Specified by Saraswati. Built by Matsya. Witnessed by Kurma.*
