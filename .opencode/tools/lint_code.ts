import { tool } from "@opencode-ai/plugin";
import path from "path";

export default tool({
  description: "Run static analysis on a Python file without executing it",
  args: {
    file_path: tool.schema.string().describe("Path to the Python file to lint"),
    rules: tool.schema.array(tool.schema.string()).optional().describe("Specific rules to check (e.g. ['E', 'F', 'W'])"),
  },
  async execute(args, context) {
    const scriptPath = path.join(context.directory, "scripts", "lint_code.sh");
    let cmd = `bash ${scriptPath} ${JSON.stringify(args.file_path)}`;
    if (args.rules && args.rules.length > 0) {
      cmd += ` --rules ${args.rules.join(",")}`;
    }
    const result = await Bun.$`${cmd}`.text();
    return result.trim();
  },
});
