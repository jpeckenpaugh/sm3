import { tool } from "@opencode-ai/plugin";

export default tool({
  description: "List files and directories matching a glob pattern",
  args: {
    pattern: tool.schema.string().describe("Glob pattern, e.g. 'backlog/*.md' or 'src/**/*.py'"),
    root: tool.schema.string().optional().default(".").describe("Root directory"),
    max_results: tool.schema.number().optional().default(200).describe("Maximum entries to return"),
  },
  async execute(args, context) {
    const root = args.root || ".";
    const cwd = process.cwd();
    process.chdir(root);
    const entries = Array.from(new Bun.Glob(args.pattern).scanSync());
    process.chdir(cwd);

    const files = entries.slice(0, args.max_results);
    return JSON.stringify({
      files,
      count: files.length,
      truncated: entries.length > args.max_results,
    });
  },
});
