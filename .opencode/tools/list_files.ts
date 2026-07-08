import { tool } from "@opencode-ai/plugin";
import path from "path";

export default tool({
  description: "List files and directories matching a glob pattern",
  args: {
    pattern: tool.schema.string().describe("Glob pattern, e.g. 'backlog/*.md' or 'src/**/*.py'"),
    root: tool.schema.string().optional().default(".").describe("Root directory"),
    max_results: tool.schema.number().optional().default(200).describe("Maximum entries to return"),
  },
  async execute(args, context) {
    const scriptPath = path.join(context.directory, "scripts", "list_files.sh");
    let cmd = `bash ${scriptPath} ${JSON.stringify(args.pattern)}`;
    if (args.root !== ".") cmd += ` --root ${JSON.stringify(args.root)}`;
    if (args.max_results !== 200) cmd += ` --max ${args.max_results}`;
    const result = await Bun.$`${cmd}`.text();
    return result.trim();
  },
});
