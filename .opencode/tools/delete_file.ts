import { tool } from "@opencode-ai/plugin";
import fs from "fs";

export default tool({
  description: "Delete a file from the filesystem",
  args: {
    file_path: tool.schema.string().describe("Path to the file to delete"),
  },
  async execute(args, context) {
    try {
      if (!fs.existsSync(args.file_path)) {
        return JSON.stringify({ error: `File not found: ${args.file_path}` });
      }
      fs.unlinkSync(args.file_path);
      return JSON.stringify({ deleted: args.file_path, success: true });
    } catch (e) {
      return JSON.stringify({ error: `Failed to delete ${args.file_path}: ${e.message}` });
    }
  },
});
