import { chromium } from 'playwright';
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function main() {
  console.log("Starting Uvicorn dashboard server...");
  const server = spawn('.venv/bin/uvicorn', [
    'main:app',
    '--app-dir', 'ui',
    '--port', '8001'
  ], {
    cwd: __dirname,
    env: { ...process.env, SM_DB_PATH: path.join(__dirname, 'matsya.db') },
    stdio: 'inherit'
  });

  // Give server time to bind
  await new Promise(r => setTimeout(r, 2000));

  const outDir = path.join(__dirname, 'demos/latest');
  const galleryDir = path.join(outDir, 'gallery');
  fs.mkdirSync(galleryDir, { recursive: true });

  console.log("Launching browser in 1280x720 video recording mode...");
  const browser = await chromium.launch({
    headless: true,
  });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: {
      dir: outDir,
      size: { width: 1280, height: 720 }
    }
  });

  const page = await context.newPage();

  try {
    // 1. SEEKDEPTH LIVE SITE (0s - 6s)
    console.log("Navigating to https://seekdepth.net/...");
    await page.goto('https://seekdepth.net/', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(1000);

    // Scroll to the archetypes section
    const imgEl = page.locator('img[alt="The Archetypes"]');
    if (await imgEl.count() > 0) {
      await imgEl.scrollIntoViewIfNeeded();
      await page.waitForTimeout(1000);
      console.log("Capturing 02-tri-archetype-pantheon.png...");
      await page.screenshot({ path: path.join(galleryDir, '02-tri-archetype-pantheon.png') });
      await page.waitForTimeout(2000);
    } else {
      await page.screenshot({ path: path.join(galleryDir, '02-tri-archetype-pantheon.png') });
    }

    // 2. OPERATOR DASHBOARD OVERVIEW (6s - 12s)
    console.log("Navigating to Operator Dashboard at http://127.0.0.1:8001/...");
    await page.goto('http://127.0.0.1:8001/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    console.log("Capturing 01-operator-dashboard-overview.png...");
    await page.screenshot({ path: path.join(galleryDir, '01-operator-dashboard-overview.png') });
    await page.waitForTimeout(2500);

    // 3. EVENT MODAL INSPECTION (12s - 17s)
    console.log("Opening event detail modal...");
    const eventRow = page.locator('table tbody tr').first();
    if (await eventRow.count() > 0) {
      await eventRow.click();
      await page.waitForTimeout(1000);
      console.log("Capturing 04-event-dispatch-inspector.png...");
      await page.screenshot({ path: path.join(galleryDir, '04-event-dispatch-inspector.png') });
      await page.waitForTimeout(2000);
      const closeBtn = page.locator('#eventModal .btn-close, #eventModal button:has-text("Close")').first();
      if (await closeBtn.count() > 0) {
        await closeBtn.click();
        await page.waitForTimeout(800);
      }
    }

    // 4. PHASES TIMELINE VIEW (17s - 22s)
    console.log("Navigating to /phases...");
    await page.goto('http://127.0.0.1:8001/phases', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1200);
    console.log("Capturing 03-sprint-phase-pipeline.png...");
    await page.screenshot({ path: path.join(galleryDir, '03-sprint-phase-pipeline.png') });
    await page.waitForTimeout(2500);

    // 5. AGENT PROFILES & PANTHEON (22s - 26s)
    console.log("Navigating to /profiles...");
    await page.goto('http://127.0.0.1:8001/profiles', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    console.log("Capturing 05-agent-profiles-permissions.png...");
    await page.screenshot({ path: path.join(galleryDir, '05-agent-profiles-permissions.png') });
    await page.waitForTimeout(2500);

    // 6. SPRINTS & RECENT RUNS (26s - 30s)
    console.log("Navigating to /sprints...");
    await page.goto('http://127.0.0.1:8001/sprints', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    console.log("Capturing 06-file-contracts-audit.png...");
    await page.screenshot({ path: path.join(galleryDir, '06-file-contracts-audit.png') });
    await page.waitForTimeout(2500);

    console.log("Scripted sequence completed successfully.");
  } catch (err) {
    console.error("Error during recording:", err);
  } finally {
    const video = page.video();
    await context.close();
    await browser.close();
    server.kill();

    if (video) {
      const videoPath = await video.path();
      const finalVideoPath = path.join(outDir, 'demo.webm');
      fs.copyFileSync(videoPath, finalVideoPath);
      console.log(`Video saved to ${finalVideoPath}`);
    }
  }
}

main().catch(console.error);
