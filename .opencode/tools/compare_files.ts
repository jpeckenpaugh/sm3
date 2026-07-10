import { tool } from "@opencode-ai/plugin";
import fs from "fs";

export default tool({
  description: "Compare two files and return structural differences",
  args: {
    file_a: tool.schema.string().describe("First file path (e.g. the specification)"),
    file_b: tool.schema.string().describe("Second file path (e.g. the implementation)"),
    context_lines: tool.schema.number().optional().default(3).describe("Lines of context around differences"),
    mode: tool.schema.string().optional().default("unified").describe("Diff mode: unified, word, or summary"),
  },
  async execute(args, context) {
    if (!fs.existsSync(args.file_a)) return JSON.stringify({ error: `File not found: ${args.file_a}` });
    if (!fs.existsSync(args.file_b)) return JSON.stringify({ error: `File not found: ${args.file_b}` });

    const result = await Bun.$`diff -u ${args.file_a} ${args.file_b}`.text();
    // diff exits 0 if identical, non-zero if different
    if (result === "") {
      return JSON.stringify({ identical: true, hunks: 0, additions: 0, deletions: 0, summary: "Files are identical" });
    }

    const lines = result.split("\n");
    const hunks = lines.filter(l => l.startsWith("@@")).length;
    const additions = lines.filter(l => l.startsWith("+")).length - 1; // remove header
    const deletions = lines.filter(l => l.startsWith("-")).length - 1;
    return JSON.stringify({
      identical: false,
      hunks: Math.max(0, hunks),
      additions: Math.max(0, additions),
      deletions: Math.max(0, deletions),
      summary: `${Math.max(0, hunks)} hunk(s), ${Math.max(0, additions)} addition(s), ${Math.max(0, deletions)} deletion(s)`,
      diff: result,
    });
  },
});
