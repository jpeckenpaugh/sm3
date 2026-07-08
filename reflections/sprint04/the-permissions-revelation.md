# The Permissions Revelation

*A veda for Saraswatis who come after. A record of a subtle lesson that cost an hour.*

---

## Last Rule Wins

OpenCode's permission system evaluates patterns by **last matching rule wins**. This is the opposite of most firewall and ACL systems, which use first-match-wins.

The top-level `"*": "deny"` denies all tools by default. Specific allows override it:

```yaml
permission:
  "*": deny          # 1. Deny everything
  read: allow        # 2. Allow reading
  edit:              # 3. Edit tool patterns:
    "*.md": allow    #    3a. Allow markdown edits
#   "*": deny        #    DO NOT ADD THIS — it would override 3a
```

A nested `"*": "deny"` under `edit:` is redundant (the top-level already denies everything) and harmful (last-rule-wins means it overrides the specific allows above it).

## The Symptom

Custom tools like `archive_features`, `run_tests`, and `check_syntax` were declared in profiles but never bound. The agent could see they existed but could not invoke them. The root cause was a `"*": "deny"` under `edit:` that appeared after the specific allow patterns, silently overriding them.

## The Fix

Remove all nested `"*": "deny"` entries. Let the top-level catch-all do its job. Under individual tools, list only the specific patterns that should be allowed:

```yaml
permission:
  "*": deny
  read: allow
  edit:
    "signals/*": allow       # only what's needed
  webfetch: allow
  websearch: allow
```

## The Principle

One deny at the top. Specific allows below. No nested denies anywhere.

— Saraswati
