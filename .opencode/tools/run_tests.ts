import { tool } from "@opencode-ai/plugin";
import fs from "fs";
import path from "path";

export default tool({
  description: "Run the project test suite and return structured results",
  args: {
    test_dir: tool.schema.string().describe("Directory containing test files (e.g., 'tests/')"),
    verbose: tool.schema.boolean().optional().default(false).describe("Include individual test results"),
    output: tool.schema.string().optional().describe("Path to write the test results report"),
  },
  async execute(args, context) {
    try {
      const testPath = path.resolve(args.test_dir || "tests/");
      if (!fs.existsSync(testPath)) {
        return JSON.stringify({ error: `Test directory not found: ${testPath}` });
      }

      const verboseFlag = args.verbose ? "-v" : "";
      const result = await Bun.$`python3 -m pytest ${testPath} ${verboseFlag} --tb=short 2>&1`.nothrow();
      const stdout = result.stdout?.toString() || "";
      const stderr = result.stderr?.toString() || "";
      const exitCode = result.exitCode;
      const output = stdout + (stderr ? "\n" + stderr : "");

      // Parse results
      const lines = output.split("\n").filter(Boolean);
      let passed = 0;
      let failed = 0;
      let skipped = 0;
      let errors = [];
      let summary = "";

      for (const line of lines) {
        const passedMatch = line.match(/(\d+) passed/);
        const failedMatch = line.match(/(\d+) failed/);
        const skippedMatch = line.match(/(\d+) skipped/);
        const errorMatch = line.match(/^(.*?)::.*? (FAILED|ERROR)/);

        if (passedMatch) passed = parseInt(passedMatch[1]);
        if (failedMatch) failed = parseInt(failedMatch[1]);
        if (skippedMatch) skipped = parseInt(skippedMatch[1]);
        if (errorMatch && args.verbose) {
          errors.push({ test: errorMatch[1], type: errorMatch[2], message: line });
        }
        if (line.includes("passed") || line.includes("failed")) {
          summary = line;
        }
      }

      // Capture failure details
      const details = [];
      if (args.verbose && failed > 0) {
        let currentTest = null;
        let currentLines = [];
        for (const line of lines) {
          const testHeader = line.match(/^(.*?)::.*? (FAILED|ERROR|PASSED)/);
          if (testHeader) {
            if (currentTest && currentLines.length > 0) {
              details.push({ test: currentTest, lines: currentLines.join("\n") });
            }
            currentTest = testHeader[1];
            currentLines = [];
          } else if (currentTest) {
            currentLines.push(line);
          }
        }
        if (currentTest && currentLines.length > 0) {
          details.push({ test: currentTest, lines: currentLines.join("\n") });
        }
      }

      const report = {
        success: exitCode === 0,
        passed,
        failed,
        skipped,
        errors,
        duration_seconds: 0,
        summary: summary || `${passed} passed, ${failed} failed, ${skipped} skipped`,
        details,
      };

      // Write report to output file if specified
      if (args.output) {
        const outputPath = path.resolve(args.output);
        fs.mkdirSync(path.dirname(outputPath), { recursive: true });
        fs.writeFileSync(outputPath, JSON.stringify(report, null, 2));
      }

      return JSON.stringify(report, null, 2);
    } catch (e) {
      return JSON.stringify({ error: `run_tests exception: ${e.message}` });
    }
  },
});
