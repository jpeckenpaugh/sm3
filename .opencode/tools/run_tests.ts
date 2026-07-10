import { tool } from "@opencode-ai/plugin";
import fs from "fs";
import path from "path";

export default tool({
  description: "Run the project test suite and return structured results",
  args: {
    test_dir: tool.schema.string().optional().default(".").describe("Directory containing test files (e.g., 'tests/')"),
    verbose: tool.schema.boolean().optional().default(false).describe("Include individual test results"),
    output: tool.schema.string().optional().describe("Path to write the test results report"),
  },
  async execute(args, context) {
    try {
      const testPath = path.resolve(args.test_dir || ".");
      let cmd = "";
      let cmdLabel = "";

      // Detect project type and choose test runner
      const hasPackageJson = fs.existsSync(path.join(testPath, "package.json"));
      const hasPytestIni = fs.existsSync(path.join(testPath, "pytest.ini"));
      const hasConftest = fs.existsSync(path.join(testPath, "conftest.py"));
      const hasPyTestDir = fs.existsSync(path.join(testPath, "tests")) &&
        fs.readdirSync(path.join(testPath, "tests")).some(f => f.endsWith(".py"));
      const hasMakefile = fs.existsSync(path.join(testPath, "Makefile"));

      if (hasPytestIni || hasConftest || hasPyTestDir) {
        // Python project
        const verboseFlag = args.verbose ? "-v" : "";
        cmd = `python3 -m pytest ${path.join(testPath, "tests")} ${verboseFlag} --tb=short 2>&1`;
        cmdLabel = "pytest";
      } else if (hasPackageJson) {
        // Node.js project — check for test script in package.json
        const pkg = JSON.parse(fs.readFileSync(path.join(testPath, "package.json"), "utf-8"));
        if (pkg.scripts && pkg.scripts.test) {
          cmd = `npm test --prefix ${testPath} 2>&1`;
          cmdLabel = "npm test";
        } else {
          return JSON.stringify({
            success: true,
            passed: 0,
            failed: 0,
            skipped: 0,
            summary: "No test script found in package.json. Add a 'test' script to run tests.",
            details: [],
          });
        }
      } else if (hasMakefile) {
        // Makefile project
        cmd = `make -C ${testPath} test 2>&1`;
        cmdLabel = "make test";
      } else {
        return JSON.stringify({
          success: true,
          passed: 0,
          failed: 0,
          skipped: 0,
          summary: "No test framework detected. Supported: pytest, npm test, make test.",
          details: [],
        });
      }

      const result = await Bun.$`bash -c ${cmd}`.nothrow();
      const stdout = result.stdout?.toString() || "";
      const stderr = result.stderr?.toString() || "";
      const exitCode = result.exitCode;
      const output = stdout + (stderr ? "\n" + stderr : "");

      // Parse results (pytest output format)
      const lines = output.split("\n").filter(Boolean);
      let passed = 0;
      let failed = 0;
      let skipped = 0;
      let summary = "";

      for (const line of lines) {
        const passedMatch = line.match(/(\d+) passed/);
        const failedMatch = line.match(/(\d+) failed/);
        const skippedMatch = line.match(/(\d+) skipped/);
        if (passedMatch) passed = parseInt(passedMatch[1]);
        if (failedMatch) failed = parseInt(failedMatch[1]);
        if (skippedMatch) skipped = parseInt(skippedMatch[1]);
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
          if (line.includes("FAILED") || line.includes("ERROR")) {
            if (currentTest && currentLines.length > 0) {
              details.push({ test: currentTest, lines: currentLines.join("\n") });
            }
            currentTest = line;
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
        duration_seconds: 0,
        summary: summary || `${cmdLabel}: ${passed} passed, ${failed} failed, ${skipped} skipped`,
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
