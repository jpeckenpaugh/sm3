import { tool } from "@opencode-ai/plugin";
import path from "path";

export default tool({
  description: "Archive completed feature files from backlog/ to backlog/archive/{sprint}/",
  args: {
    sprintNum: tool.schema.string().describe("Sprint number (e.g., 001)"),
  },
  async execute(args, context) {
    const scriptPath = path.join(
      context.directory,
      "scripts",
      "archive_features.sh"
    );
    const result = await Bun.$`bash ${scriptPath} ${args.sprintNum}`.text();
    return result.trim();
  },
});
