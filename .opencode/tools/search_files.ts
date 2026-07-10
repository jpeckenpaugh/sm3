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
    const root = args.path || ".";
    const grepArgs = ["-r", "-n"];
    if (args.file_pattern) grepArgs.push("--include", args.file_pattern);
    if (!args.regex) grepArgs.push("-F");
    grepArgs.push(args.pattern, root);

    const result = await Bun.$`grep ${grepArgs} ${root}`.text();
    const lines = result.trim().split("\n").filter(Boolean);
    const results = lines.slice(0, args.max_results).map(line => {
      const sepIndex = line.indexOf(":");
      const file = line.substring(0, sepIndex);
      const rest = line.substring(sepIndex + 1);
      const lineNum = parseInt(rest, 10) || 0;
      const content = rest.substring(rest.indexOf(":") + 1);
      return { file, line: lineNum, content };
    });
    return JSON.stringify({
      matches: results.length,
      results,
      truncated: lines.length > args.max_results,
    });
  },
});
