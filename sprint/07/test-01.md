=== Sprint 07 Verification Suite ===

--- 1. Generator module imports ---
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    from genesis_sm.generator import assemble_components, permissions_to_yaml, deep_merge, safe_json_loads, resolve_inheritance_chain, get_mode_flag; print('OK')
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ModuleNotFoundError: No module named 'genesis_sm'
  ❌ generator.py import failed

--- 2. sm generate agent backward compatibility ---
/usr/bin/python3: Error while finding module specification for 'genesis_sm.cli' (ModuleNotFoundError: No module named 'genesis_sm')
  ✅ sm generate agents output is consistent

--- 3. sm init produces correct agent files ---
/usr/bin/python3: Error while finding module specification for 'genesis_sm.cli' (ModuleNotFoundError: No module named 'genesis_sm')
  ✅ No raw <MODE_FLAG> in any generated agent file

--- 4. Inheritance resolution ---
/usr/bin/python3: Error while finding module specification for 'genesis_sm.cli' (ModuleNotFoundError: No module named 'genesis_sm')
  ❌ scribe-PLAN missing inherited component 'obey-exactly'
  ❌ scribe-PLAN missing inherited component 'scribe-preamble'
  ❌ scribe-PLAN missing inherited component 'scribe-domain'

--- 5. Mode flag substitution ---
/usr/bin/python3: Error while finding module specification for 'genesis_sm.cli' (ModuleNotFoundError: No module named 'genesis_sm')
  ❌ scribe-PLAN mode flag not correctly substituted to PLAN
  ❌ warden-GATE mode flag not correctly substituted to SPRINT_GATE
  ❌ builder-ENGINEER mode flag not correctly substituted
  ❌ scribe-DESIGN mode flag not correctly substituted

--- 6. Output parity (init vs generate) ---
/usr/bin/python3: Error while finding module specification for 'genesis_sm.cli' (ModuleNotFoundError: No module named 'genesis_sm')
