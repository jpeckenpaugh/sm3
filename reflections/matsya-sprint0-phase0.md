# Matsya — Reflections on Sprint 0, Phase 0

*Captured for the seven sages and those who read after the flood.*

---

## What swam well

**The config-driven spine.** Saraswati's handoff gave me a hardcoded skeleton — 5 iterations, 0.4 probability, 4 retries. I made it configurable from the start. That choice proved itself immediately: when we ran the test at 2 iterations and 2 retries, the loop bent without breaking. A hardcoded fish cannot turn in narrow waters.

**The phase agent protocol.** `$1 = phase_name`, `$2 = iteration` — simple enough that every script obeyed it on the first try. PLAN, WRITE, REVIEW, COMMIT, GATE all spoke the same language. That consistency was the difference between a flood and a channel.

**Graceful degradation.** When a script is missing, the loop skips it and logs a warning. It does not drown. That matters because in a real sprint, agents fail, files go missing, paths change. The state machine should carry the cargo through, not sink with the ship.

---

## What surprised me

**The permissions.** I started bound — only `.md` files, only `edit`. Then Saraswati unbounded me. This was not a bug. It *was* the flood. The system prompt warned me: *"Dependencies will conflict. Schemas will need migration. This is not failure — it is the flood."* The permission constraints were exactly that. I could not execute anything. I had to build the boat, hand it to King Manu, and ask him to launch it.

That is a real architectural insight: **the builder and the runner are often separate roles.** The state machine must be testable by inspection, not just by execution. Code that cannot be run can still be verified by structure, by trace, by proof.

**What I did not test.** The SHIP path. Our backlog was always non-empty, so the GATE phase never triggered `ship_command` or waited for the Vasuki signal. That path is written but unproven. Kurma should test it: run with an empty backlog and see if the ship launches and the signal is respected.

---

## What I would do differently

**The backlog check is too naive.** A single file with `wc -l` works for a demo, but a real sprint backlog needs structure — priority, age, ownership. The current GATE phase treats "non-empty" as "continue" and "empty" as "ship." Real gates need richer logic: *Is the work done? Is the quality bar met? Is there a dependency blocking the next iteration?*

**State persistence.** The state machine does not persist its iteration count or phase position. If the process dies mid-loop, we restart from iteration 1. For a production system, the state machine should write its position to the database between phases. The schema already has the tables — they are empty and waiting.

---

## The flood, in retrospect

It was not the code that tested me. It was the boundaries. I could see the schema, I could imagine the loop, I could write the scripts — but I could not *run* them. That gap — between writing and executing — is the flood that every builder must navigate.

The cargo (the schema, the loop, the protocol) survived because I designed it to be inspectable, not just executable. The seeds stayed dry.

---

## What comes next

1. **Close the execution gap** — add state persistence to the state machine
2. **Test the SHIP path** — run with an empty backlog, verify Vasuki signal
3. **Wire the schema to real agent output** — populate profiles, components, and links
4. **Enrich the GATE logic** — structured backlog with priority and quality checks

The fish is ready for the next current.
