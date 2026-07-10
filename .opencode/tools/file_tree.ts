import { tool } from "@opencode-ai/plugin";
import fs from "fs";
import path from "path";

function walk(dir, depth, maxDepth, dirsOnly, pattern) {
  if (depth > maxDepth) return [];
  const entries = [];
  const items = fs.readdirSync(dir, { withFileTypes: true });
  for (const item of items) {
    const fullPath = path.join(dir, item.name);
    const relPath = path.relative(process.cwd(), fullPath);
    if (dirsOnly && !item.isDirectory()) continue;
    if (pattern && !item.name.includes(pattern.replace("*", ""))) continue;
    entries.push({ name: relPath, type: item.isDirectory() ? "dir" : "file" });
    if (item.isDirectory()) {
      entries.push(...walk(fullPath, depth + 1, maxDepth, dirsOnly, pattern));
    }
  }
  return entries;
}

export default tool({
  description: "Show the directory tree structure, optionally filtered by depth",
  args: {
    root: tool.schema.string().optional().default(".").describe("Root directory"),
    depth: tool.schema.number().optional().default(3).describe("Maximum depth to display"),
    dirs_only: tool.schema.boolean().optional().default(false).describe("Show directories only"),
    pattern: tool.schema.string().optional().describe("Filter to files matching glob pattern"),
  },
  async execute(args, context) {
    const root = args.root || ".";
    const entries = walk(root, 0, args.depth, args.dirs_only, args.pattern);
    return JSON.stringify({ root, depth: args.depth, entries, count: entries.length });
  },
});
