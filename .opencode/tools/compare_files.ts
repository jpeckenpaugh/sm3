import { tool } from "@opencode-ai/plugin";
import path from "path";

export default tool({
  description: "Compare two files and return structural differences",
  args: {
    file_a: tool.schema.string().describe("First file path (e.g. the specification)"),
    file_b: tool.schema.string().describe("Second file path (e.g. the implementation)"),
    context_lines: tool.schema.number().optional().default(3).describe("Lines of context around differences"),
    mode: tool.schema.string().optional().default("unified").describe("Diff mode: unified, word, or summary"),
  },
  async execute(args, context) {
    const scriptPath = path.join(context.directory, "scripts", "compare_files.sh");
    let cmd = `bash ${scriptPath} ${JSON.stringify(args.file_a)} ${JSON.stringify(args.file_b)}`;
    if (args.context_lines !== 3) cmd += ` --context ${args.context_lines}`;
    if (args.mode !== "unified") cmd += ` --mode ${args.mode}`;
    const result = await Bun.$`${cmd}`.text();
    return result.trim();
  },
});
