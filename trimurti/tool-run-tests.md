# Tool: `run_tests`

*A single-purpose bridge between the warden's watching and the test suite it must observe.*

---

## The Problem

warden-TEST_RUN is tasked with running tests and reporting results. But the warden has no `bash: allow` and no `python: allow`. It cannot execute `pytest` or any test runner. It can only read test files and produce reports from static analysis — guessing whether tests would pass, fail, or error.

This is theatre, not testing. The TEST_RUN phase exists to produce *real* results, not speculative ones.

The `run_tests` tool bridges this gap. It executes the project's test suite in a controlled, bounded way and returns structured results. The warden never gains a shell — it gains a single-purpose tool that does one thing: run tests and report results.

## The Tool

### Definition

A custom tool in `.opencode/tools/run_tests.ts` that invokes `pytest` against the project's test directory and returns structured output.

### Tool signature

```typescript
import { tool } from "@opencode-ai/plugin";
import path from "path";

export default tool({
  description: "Run the project test suite and return structured results",
  args: {
    testDir: tool.schema.string()
      .describe("Directory containing test files (e.g., 'tests/')"),
    verbose: tool.schema.boolean()
      .optional()
      .default(false)
      .describe("Include individual test results"),
    timeout: tool.schema.number()
      .optional()
      .default(120)
      .describe("Maximum execution time in seconds"),
  },
  async execute(args, context) {
    const testPath = path.join(context.directory, args.testDir);
    const verboseFlag = args.verbose ? "-v" : "";
    
    // Run pytest in the project directory
    // The project's .venv is assumed to have pytest installed
    const result = await Bun.$`
      cd ${context.directory}
      python3 -m pytest ${testPath} ${verboseFlag} -x --tb=short 2>&1
    `.text();
    
    // Parse the output into structured results
    return parseTestResults(result, args.verbose);
  },
});
```

### Return format

```json
{
  "success": true,
  "passed": 32,
  "failed": 0,
  "skipped": 0,
  "errors": [],
  "duration_seconds": 2.3,
  "summary": "32 passed in 2.30s",
  "details": []
}
```

On failure:

```json
{
  "success": false,
  "passed": 28,
  "failed": 3,
  "skipped": 1,
  "errors": [
    {
      "test": "tests/test_main.py::TestRootEndpoint::test_root_returns_200",
      "type": "AssertionError",
      "message": "assert 404 == 200",
      "line": 42
    }
  ],
  "duration_seconds": 1.8,
  "summary": "28 passed, 3 failed, 1 skipped in 1.80s"
}
```

### How the agent invokes it

The warden-TEST_RUN agent calls the tool as part of its mode-specific instructions:

```markdown
### Running Tests

Call the `run_tests` tool with:
  testDir = "tests/"
  verbose = true

Read the results. If all tests pass, produce a test report at OUTPUT1.
If tests fail, include the failure details in the report and
write .escalation/TEST_RUN/<reason>.md for critical failures.
```

### Permission

The tool is available to `warden-TEST_RUN` via the agent profile:

```json
{
  "permissions": {
    "run_tests": "allow"
  }
}
```

No `bash: allow`. No `python: allow`. The tool is the boundary.

## What It Enables

| Before | After |
|--------|-------|
| warden reads test files and guesses if they pass | warden runs tests and reports real results |
| TEST_RUN phase produces speculative reports | TEST_RUN phase produces verified results |
| REVIEW phase cannot trust test results | REVIEW phase receives validated test data |
| Broken tests discovered in later phases | Broken tests caught and reported immediately |

## Non-Goals

- Installing test dependencies (assumes pytest is installed in .venv)
- Running specific subsets of tests (runs the full test directory)
- Modifying test files or source code
- Providing coverage analysis (beyond what pytest reports)
- Running in parallel or distributed mode

## Backward Compatibility

If `.opencode/tools/run_tests.ts` does not exist, the agent cannot call the tool.
The phase continues but produces a warning. Graceful degradation.

---

*Specified by Saraswati. Built by Matsya. Used by warden-TEST_RUN. Watched by Kurma.*
