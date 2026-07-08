# Feature: Profile Cleanup — Extract CONFIRM_BOOTSTRAP into Shared Component

*Eliminate 150 lines of duplicated boilerplate. Single source of truth for the handshake protocol.*

---

## The Problem

Every mode-specific component contains 15–20 lines of identical CONFIRM_BOOTSTRAP boilerplate:

```
## Strict Behavior Rules

All prompts must start with one of the following MODE_FLAG strings: ...

## Mode Flags

### CONFIRM_BOOTSTRAP

If the user sends CONFIRM_BOOTSTRAP flag in their message, you must respond with:
"BOOTSTRAP CONFIRMED. Available MODE_FLAG values are ..."
```

This exact text is duplicated across 10 mode-specific components. If the handshake format changes (as it did with Mahadevi's Pulse Check), all 10 must be updated individually — and they likely already diverge.

## The Fix

### 1. Create `components/rules/bootstrap-protocol.json`

A single shared component containing the HANDSHAKE protocol:

```json
{
  "type": "rule",
  "name": "bootstrap-protocol",
  "content": "## Strict Behavior Rules\n\nAll prompts must start with one of the following MODE_FLAG strings: `CONFIRM_BOOTSTRAP`, `<MODE_FLAG>`. There are exclusively 2 MODE_FLAG values that are valid. Each has separate behaviors. See below for required responses based upon input MODE_FLAG.\n\n## Mode Flags\n\n### CONFIRM_BOOTSTRAP\n\nIf the user sends CONFIRM_BOOTSTRAP flag in their message, you must respond with:\n\n\"BOOTSTRAP CONFIRMED. Available MODE_FLAG values are CONFIRM_BOOTSTRAP, <MODE_FLAG>\"\n\n### <MODE_FLAG>\n\nIf the user sends <MODE_FLAG> in their message, follow the logic as outlined below.\n"
}
```

The `<MODE_FLAG>` placeholder is resolved at generation time by `cmd_generate_agent()` — substituted with the actual mode name before the component content is rendered into the agent body.

### 2. Update `_assemble_components_for_profiles()` in `cli.py`

After collecting all component content, substitute `<MODE_FLAG>` with the actual mode flag. The mode flag is the agent's name suffix — e.g., for `scribe-PLAN`, the mode flag is `PLAN`.

```python
def _substitute_mode_flag(body_parts, mode_flag):
    """Replace <MODE_FLAG> placeholder with the actual mode flag."""
    return [part.replace("<MODE_FLAG>", mode_flag) for part in body_parts]
```

The mode flag can be derived from the profile name: `profile_name.split("-")[-1]` — e.g., `scribe-PLAN` → `PLAN`, `warden-SPRINT_GATE` → `SPRINT_GATE`.

### 3. Add `rule/bootstrap-protocol` to all derived profile-component links

Update `profile-components/*.json` for each derived profile to include the shared bootstrap component at `order_idx: 0` (before the mode-specific component). Example — `profile-components/scribe-PLAN.json`:

```json
{
  "profile": "scribe-PLAN",
  "components": [
    { "type": "rule", "name": "bootstrap-protocol", "order_idx": 0 },
    { "type": "prompt", "name": "scribe-mode-plan", "order_idx": 1 }
  ]
}
```

### 4. Remove the CONFIRM_BOOTSTRAP section from all mode-specific components

This means editing 10 `components/prompts/*.json` files to delete the first ~20 lines of boilerplate from each, leaving only the mode-specific instructions.

### Files to delete boilerplate from

| Component | Lines removed |
|-----------|---------------|
| `scribe-mode-plan` | ~20 |
| `scribe-mode-design` | ~20 |
| `scribe-mode-architect` | ~20 |
| `scribe-mode-review` | ~20 |
| `scribe-mode-sprint-planning` | ~20 |
| `builder-mode-engineer` | ~20 |
| `builder-mode-test` | ~20 |
| `warden-mode-review` | ~20 |
| `warden-mode-test-run` | ~20 |
| `warden-mode-gate` | ~20 |

### Verification

1. Generate a derived agent and confirm the frontmatter + body includes the CONFIRM_BOOTSTRAP section with the correct mode flag.
2. Confirm the mode-specific content no longer contains the boilerplate.
3. Confirm that `warden-TEST_RUN.md` responds with "Available MODE_FLAG values are CONFIRM_BOOTSTRAP, TEST_RUN" (not a literal `<MODE_FLAG>`).

---

*Specified by Saraswati. Built by Matsya. Witnessed by Kurma.*
