import { tool } from "@opencode-ai/plugin";
import path from "path";

export default tool({
  description: "Search file contents using a literal or regex pattern",
  args: {
    pattern: tool.schema.string().describe("Search pattern (literal or regex)"),
    path: tool.schema.string().optional().default(".").describe("Root directory to search"),
    file_pattern: tool.schema.string().optional().describe("File glob pattern, e.g. '*.md' or '*.py'"),
    regex: tool.schema.boolean().optional().default(false).describe("Treat pattern as regex"),
    max_results: tool.schema.number().optional().default(50).describe("Maximum results to return"),
  },
  async execute(args, context) {
    const scriptPath = path.join(context.directory, "scripts", "search_files.sh");
    let cmd = `bash ${scriptPath} ${JSON.stringify(args.pattern)}`;
    if (args.path !== ".") cmd += ` --path ${JSON.stringify(args.path)}`;
    if (args.file_pattern) cmd += ` --include ${JSON.stringify(args.file_pattern)}`;
    if (args.regex) cmd += ` --regex`;
    if (args.max_results !== 50) cmd += ` --max ${args.max_results}`;
    const result = await Bun.$`${cmd}`.text();
    return result.trim();
  },
});
