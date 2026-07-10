import { tool } from "@opencode-ai/plugin";
import fs from "fs";

export default tool({
  description: "Run static analysis on a Python file without executing it",
  args: {
    file_path: tool.schema.string().describe("Path to the Python file to lint"),
    rules: tool.schema.array(tool.schema.string()).optional().describe("Specific rules to check (e.g. ['E', 'F', 'W'])"),
  },
  async execute(args, context) {
    try {
      if (!fs.existsSync(args.file_path)) {
        return JSON.stringify({ error: `File not found: ${args.file_path}` });
      }

      // Check if pyflakes is available
      const whichResult = await Bun.$`which pyflakes`.nothrow();
      const pyflakesAvailable = whichResult.exitCode === 0;

      if (pyflakesAvailable) {
        const pyflakesResult = await Bun.$`pyflakes ${args.file_path}`.nothrow();
        const pyflakesStdout = (pyflakesResult.stdout?.toString() || "").trim();
        const exitCode = pyflakesResult.exitCode;

        if (exitCode === 0) {
          return JSON.stringify({ file: args.file_path, valid: true, issues: [], error_count: 0, warning_count: 0, style_count: 0 });
        }

        if (pyflakesStdout) {
          const lines = pyflakesStdout.split("\n").filter(Boolean);
          let errors = 0;
          let warnings = 0;
          const issues = lines.map(line => {
            const parts = line.split(":");
            const message = parts.slice(3).join(":").trim();
            const code = message.split(/\s+/)[0];
            const isError = ["F821", "F822", "F823", "F831"].includes(code);
            if (isError) errors++; else warnings++;
            return {
              line: parseInt(parts[1]) || 0,
              column: parseInt(parts[2]) || 0,
              code,
              message,
              severity: isError ? "error" : "warning",
            };
          });
          return JSON.stringify({
            file: args.file_path,
            valid: false,
            issues,
            error_count: errors,
            warning_count: warnings,
            style_count: 0,
          });
        }
      }

      // Fallback: check syntax with python3 -m py_compile
      const checkResult = await Bun.$`python3 -m py_compile ${args.file_path}`.nothrow();
      if (checkResult.exitCode === 0) {
        return JSON.stringify({ file: args.file_path, valid: true, issues: [], error_count: 0, warning_count: 0, style_count: 0 });
      }
      const checkStderr = (checkResult.stderr?.toString() || "").trim();
      return JSON.stringify({
        file: args.file_path,
        valid: false,
        issues: [{ line: 0, column: 0, code: "E000", message: checkStderr || "Syntax error", severity: "error" }],
        error_count: 1,
        warning_count: 0,
        style_count: 0,
      });
    } catch (e) {
      return JSON.stringify({ error: `lint_code exception: ${e.message}` });
    }
  },
});
