import { tool } from "@opencode-ai/plugin";
import path from "path";
import fs from "fs";

export default tool({
  description: "Read the pulse history of the container from the database",
  args: {
    db_path: tool.schema.string().optional().describe("Path to matsya.db (auto-detected if not provided)"),
  },
  async execute(args, context) {
    let dbPath = args.db_path;
    if (!dbPath) {
      const candidates = ["matsya.db", "test-project.db"];
      for (const c of candidates) {
        if (fs.existsSync(c)) { dbPath = c; break; }
      }
    }
    if (!dbPath) {
      return JSON.stringify({ error: "Database not found" });
    }

    const sql = `
      SELECT
        (SELECT COUNT(*) FROM sprints) AS sprint_count,
        (SELECT MAX(completed_at) FROM phase_runs) AS last_pulse_at,
        (SELECT COUNT(*) FROM dispatch_log) AS dispatch_count,
        (SELECT number FROM sprints ORDER BY id DESC LIMIT 1) AS active_sprint,
        (SELECT status FROM sprints ORDER BY id DESC LIMIT 1) AS active_sprint_status
    `;

    const result = await Bun.$`sqlite3 -json ${dbPath} ${sql}`.text();

    const data = JSON.parse(result);
    // Compute silence duration
    if (data.last_pulse_at) {
      const now = new Date();
      const last = new Date(data.last_pulse_at);
      const silence = Math.floor((now.getTime() - last.getTime()) / 1000);
      data.silence_seconds = silence;
      const h = Math.floor(silence / 3600);
      const m = Math.floor((silence % 3600) / 60);
      data.silence_human = h > 0 ? `${h}h ${m}m` : `${m}m`;
    } else {
      data.silence_human = "no pulses recorded";
    }
    data.db_path = dbPath;
    return JSON.stringify(data, null, 2);
  },
});
