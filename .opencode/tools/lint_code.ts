import { tool } from "@opencode-ai/plugin";
import fs from "fs";
import path from "path";

export default tool({
  description: "Run static analysis on a Python file without executing it",
  args: {
    file_path: tool.schema.string().describe("Path to the file to lint"),
    rules: tool.schema.array(tool.schema.string()).optional().describe("Specific rules to check (e.g. ['E', 'F', 'W'])"),
  },
  async execute(args, context) {
    try {
      if (!fs.existsSync(args.file_path)) {
        return JSON.stringify({ error: `File not found: ${args.file_path}` });
      }

      const ext = path.extname(args.file_path).toLowerCase();

      // Python: pyflakes or py_compile
      if (ext === ".py") {
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

        // Python fallback: py_compile
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
      }

      // JavaScript / TypeScript: eslint
      if (ext === ".js" || ext === ".jsx" || ext === ".ts" || ext === ".tsx") {
        const whichEslint = await Bun.$`which npx`.nothrow();
        if (whichEslint.exitCode === 0) {
          const eslintResult = await Bun.$`npx eslint ${args.file_path} --format json --no-ignore`.nothrow();
          const eslintStdout = (eslintResult.stdout?.toString() || "").trim();
          if (eslintStdout) {
            try {
              const parsed = JSON.parse(eslintStdout);
              if (Array.isArray(parsed) && parsed.length > 0) {
                const issues = parsed[0].messages || [];
                const mapped = issues.map(m => ({
                  line: m.line || 0,
                  column: m.column || 0,
                  code: m.ruleId || "unknown",
                  message: m.message || "",
                  severity: m.severity === 2 ? "error" : "warning",
                }));
                return JSON.stringify({
                  file: args.file_path,
                  valid: mapped.filter(m => m.severity === "error").length === 0,
                  issues: mapped,
                  error_count: mapped.filter(m => m.severity === "error").length,
                  warning_count: mapped.filter(m => m.severity === "warning").length,
                  style_count: 0,
                });
              }
            } catch { /* not JSON, fall through */ }
          }
        }
        // No linter available — return valid with a notice
        return JSON.stringify({
          file: args.file_path,
          valid: true,
          issues: [],
          notice: "No linter configured for this file type. Install eslint for JS/TS.",
          error_count: 0,
          warning_count: 0,
          style_count: 0,
        });
      }

      // HTML: htmlhint
      if (ext === ".html") {
        const whichHtmlhint = await Bun.$`which npx`.nothrow();
        if (whichHtmlhint.exitCode === 0) {
          const htmlResult = await Bun.$`npx htmlhint ${args.file_path} 2>&1`.nothrow();
          // htmlhint outputs plain text; parse if available
          const htmlStdout = (htmlResult.stdout?.toString() || "").trim();
          if (htmlStdout && htmlResult.exitCode !== 0) {
            const lines = htmlStdout.split("\n").filter(Boolean).filter(l => l.includes(":"));
            const issues = lines.map(l => ({
              line: 0,
              column: 0,
              code: "htmlhint",
              message: l.trim(),
              severity: "warning",
            }));
            return JSON.stringify({
              file: args.file_path,
              valid: false,
              issues,
              error_count: 0,
              warning_count: issues.length,
              style_count: 0,
            });
          }
        }
        return JSON.stringify({
          file: args.file_path,
          valid: true,
          issues: [],
          notice: "No linter configured for HTML. Install htmlhint to check markup.",
          error_count: 0,
          warning_count: 0,
          style_count: 0,
        });
      }

      // CSS / SCSS
      if (ext === ".css" || ext === ".scss") {
        const whichStylelint = await Bun.$`which npx`.nothrow();
        if (whichStylelint.exitCode === 0) {
          const cssResult = await Bun.$`npx stylelint ${args.file_path} 2>&1`.nothrow();
          const cssStdout = (cssResult.stdout?.toString() || "").trim();
          if (cssStdout && cssResult.exitCode !== 0) {
            try {
              const parsed = JSON.parse(cssStdout);
              if (parsed.length > 0) {
                const issues = (parsed[0].warnings || []).map(w => ({
                  line: w.line || 0,
                  column: w.column || 0,
                  code: w.rule || "unknown",
                  message: w.text || "",
                  severity: w.severity === "error" ? "error" : "warning",
                }));
                return JSON.stringify({
                  file: args.file_path,
                  valid: issues.filter(i => i.severity === "error").length === 0,
                  issues,
                  error_count: issues.filter(i => i.severity === "error").length,
                  warning_count: issues.filter(i => i.severity === "warning").length,
                  style_count: 0,
                });
              }
            } catch { /* fall through */ }
          }
        }
        return JSON.stringify({
          file: args.file_path,
          valid: true,
          issues: [],
          notice: "No linter configured for CSS. Install stylelint to check styles.",
          error_count: 0,
          warning_count: 0,
          style_count: 0,
        });
      }

      // Unsupported file type
      return JSON.stringify({
        file: args.file_path,
        valid: true,
        issues: [],
        notice: `No linter available for file type '${ext}'. Supported: .py, .js, .ts, .html, .css, .scss`,
        error_count: 0,
        warning_count: 0,
        style_count: 0,
      });
    } catch (e) {
      return JSON.stringify({ error: `lint_code exception: ${e.message}` });
    }
  },
});
