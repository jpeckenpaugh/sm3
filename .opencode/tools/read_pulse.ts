import { tool } from "@opencode-ai/plugin";
import path from "path";

export default tool({
  description: "Read the pulse history of the container from the database",
  args: {
    db_path: tool.schema.string().optional().describe("Path to matsya.db (auto-detected if not provided)"),
  },
  async execute(args, context) {
    const scriptPath = path.join(context.directory, "scripts", "read_pulse.sh");
    let cmd = `bash ${scriptPath}`;
    if (args.db_path) cmd += ` --db ${JSON.stringify(args.db_path)}`;
    const result = await Bun.$`${cmd}`.text();
    return result.trim();
  },
});
