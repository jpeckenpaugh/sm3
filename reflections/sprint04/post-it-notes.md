# Post-It Notes for the Next Scribe

*Low-entropy, high-impact breadcrumbs from Sprint 04. Stick these on the edge of your desk.*

---

## 1. Every mode component needs a CONFIRM_BOOTSTRAP section

If an agent profile mentions `CONFIRM_BOOTSTRAP` in its Strict Behavior Rules, it must also have a section defining the response format:

```
### CONFIRM_BOOTSTRAP

If the user sends CONFIRM_BOOTSTRAP flag in their message, you must respond with:
"BOOTSTRAP CONFIRMED. Available MODE_FLAG values are CONFIRM_BOOTSTRAP, <MODE>"
```

Without this, the handshake protocol returns empty mode flags and the agent cannot confirm it understood its role.

## 2. Last rule wins

OpenCode permissions are evaluated **last matching rule wins**. Put the broad `"*": "deny"` at the top of `permissions:`, then specific allows below. Never put a `"*": "deny"` inside a nested tool block — it will override the allows above it.

## 3. tools: header is not a thing

Custom tools in `.opencode/tools/` are automatically available to all agents. You do not need a `tools:` declaration in the agent profile. The permission is declared inline in `permissions:`:

```yaml
permission:
  "*": deny
  run_tests: allow    # not tools: [run_tests]
```

## 4. Agents in non-interactive sessions cannot use `question`

If an agent calls `question` and there is no human to answer, the question hangs forever. Only grant `question` to Spiral 5 agents (Saraswati, Matsya, Kurma). Spiral 1 agents run in the state machine and never get it.

## 5. Signals are not temp files

Signals carry the temperature of discussions between the three aspects. Never delete them with `git add -A`. Archive them with `scripts/archive-signals.sh` after all three have acknowledged them.

## 6. Webbfetch URL patterns don't work in agent profiles

You cannot filter webfetch by URL pattern in the agent's permission block. `webfetch` is either fully allowed or fully denied. For domain filtering, use a proxy (see ft017).

## 7. When adding a new derived profile, check three places

1. `profiles/<name>.json` — the profile definition
2. `components/prompts/<mode>.json` — the mode-specific component content
3. `pipeline_states` seed data — the state-to-agent mapping

All three must be in sync. If any one is missing, the agent won't dispatch.

## 8. The engine is generic — it doesn't care how many states

Adding a state means adding rows to `pipeline_states` and `pipeline_transitions`. No Python changes. The engine reads from the database at startup.

## 9. Test the handshake first

Before wiring a new agent into the full pipeline, test that CONFIRM_BOOTSTRAP works:

```python
from pipeline.dispatch import dispatch_sync
result = dispatch_sync(agent_name="scribe-DESIGN", request_text="CONFIRM_BOOTSTRAP")
print(result.confirmed_modes)  # Should include DESIGN
```

If `confirmed_modes` is empty, the profile is missing the CONFIRM_BOOTSTRAP response format.

## 10. Escalation files go in .escalation/<STATE>/<reason>.md

The engine checks for escalation files after every phase. If a phase script (or agent) detects a problem it cannot solve, it writes `.escalation/PLAN/ambiguous-scope.md` with a description. The engine pauses the sprint, sets status to `blocked`, and waits for Kurma.

No special permissions needed — the engine reads the file path directly.

---

*Written from the swan's back, looking down at four sprints of accumulated wisdom. Use freely. The moon is in the water.*
