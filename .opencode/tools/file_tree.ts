import { tool } from "@opencode-ai/plugin";
import path from "path";

export default tool({
  description: "Show the directory tree structure, optionally filtered by depth",
  args: {
    root: tool.schema.string().optional().default(".").describe("Root directory"),
    depth: tool.schema.number().optional().default(3).describe("Maximum depth to display"),
    dirs_only: tool.schema.boolean().optional().default(false).describe("Show directories only"),
    pattern: tool.schema.string().optional().describe("Filter to files matching glob pattern"),
  },
  async execute(args, context) {
    const scriptPath = path.join(context.directory, "scripts", "file_tree.sh");
    let cmd = `bash ${scriptPath}`;
    if (args.root !== ".") cmd += ` --root ${JSON.stringify(args.root)}`;
    if (args.depth !== 3) cmd += ` --depth ${args.depth}`;
    if (args.dirs_only) cmd += ` --dirs-only`;
    if (args.pattern) cmd += ` --pattern ${JSON.stringify(args.pattern)}`;
    const result = await Bun.$`${cmd}`.text();
    return result.trim();
  },
});
