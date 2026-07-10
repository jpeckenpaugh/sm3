import { tool } from "@opencode-ai/plugin";
import fs from "fs";
import path from "path";

export default tool({
  description: "Archive completed feature files from backlog/ to backlog/archive/{sprint}/",
  args: {
    sprintNum: tool.schema.string().describe("Sprint number (e.g., 001)"),
  },
  async execute(args, context) {
    const sprintNum = String(args.sprintNum).padStart(2, "0");
    const featuresDir = path.join("sprint", sprintNum, "features");
    const backlogDir = "backlog";
    const archiveDir = path.join("backlog", "archive", sprintNum);

    if (!fs.existsSync(featuresDir)) {
      return `No features directory found at ${featuresDir} — nothing to archive.`;
    }

    fs.mkdirSync(archiveDir, { recursive: true });
    let archived = 0;
    let notFound = 0;

    const featureFiles = fs.readdirSync(featuresDir).filter(f => f.startsWith("ft-") && f.endsWith(".md"));
    for (const fname of featureFiles) {
      const src = path.join(backlogDir, fname);
      if (fs.existsSync(src)) {
        fs.renameSync(src, path.join(archiveDir, fname));
        archived++;
      } else {
        notFound++;
      }
    }

    return `✓ Archive complete: ${archived} feature(s) archived, ${notFound} not found in backlog.`;
  },
});
