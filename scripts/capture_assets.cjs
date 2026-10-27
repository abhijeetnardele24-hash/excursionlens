/**
 * scripts/capture_assets.cjs — Automated Real Screenshot & Asset Generator
 *
 * Captures the 5 required product screenshots and renders the architecture diagram & Devpost thumbnail.
 */

const { chromium } = require('@playwright/test');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const SCREENSHOTS_DIR = path.resolve(__dirname, '..', 'docs', 'assets', 'screenshots');
const ASSETS_DIR = path.resolve(__dirname, '..', 'docs', 'assets');

async function main() {
  fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });

  console.log('🚀 Starting ExcursionLens backend for asset capture...');
  const server = spawn('.\\.venv\\Scripts\\python.exe', ['-m', 'uvicorn', 'apps.api.app.main:app', '--port', '8000', '--host', '127.0.0.1'], {
    stdio: 'ignore',
    shell: true,
  });

  // Wait for server to boot
  await new Promise((resolve) => setTimeout(resolve, 2500));

  const browser = await chromium.launch({ headless: true });

  try {
    // 1. Render architecture.png from architecture.svg if svg exists
    const svgPath = path.join(ASSETS_DIR, 'architecture.svg');
    const archPngPath = path.join(ASSETS_DIR, 'architecture.png');
    if (fs.existsSync(svgPath)) {
      console.log('Rendering docs/assets/architecture.png at 2x Retina resolution...');
      const archPage = await browser.newPage({
        viewport: { width: 1100, height: 680 },
        deviceScaleFactor: 2,
      });
      const svgContent = fs.readFileSync(svgPath, 'utf-8');
      await archPage.setContent(`
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8">
            <style>
              * { box-sizing: border-box; margin: 0; padding: 0; }
              body { background: #17201E; overflow: hidden; width: 1100px; height: 680px; }
              #svg-container { width: 1100px; height: 680px; display: block; }
              svg { width: 1100px; height: 680px; display: block; }
            </style>
          </head>
          <body>
            <div id="svg-container">
              ${svgContent}
            </div>
          </body>
        </html>
      `);
      const svgElem = archPage.locator('#svg-container');
      await svgElem.screenshot({ path: archPngPath });
      await archPage.close();
      console.log('✅ architecture.png rendered (2200x1360).');
    }

    // 2. Render Devpost Thumbnail at 1280x720
    const thumbSvgPath = path.join(ASSETS_DIR, 'thumbnail.svg');
    const thumbPngPath = path.join(ASSETS_DIR, 'excursionlens-devpost-thumbnail.png');
    if (fs.existsSync(thumbSvgPath)) {
      console.log('Rendering docs/assets/excursionlens-devpost-thumbnail.png (1280x720)...');
      const thumbPage = await browser.newPage({
        viewport: { width: 1280, height: 720 },
        deviceScaleFactor: 1,
      });
      const thumbSvgContent = fs.readFileSync(thumbSvgPath, 'utf-8');
      await thumbPage.setContent(`
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8">
            <style>
              * { box-sizing: border-box; margin: 0; padding: 0; }
              body { background: #17201E; overflow: hidden; width: 1280px; height: 720px; }
              #thumb-container { width: 1280px; height: 720px; display: block; }
              svg { width: 1280px; height: 720px; display: block; }
            </style>
          </head>
          <body>
            <div id="thumb-container">
              ${thumbSvgContent}
            </div>
          </body>
        </html>
      `);
      const thumbElem = thumbPage.locator('#thumb-container');
      await thumbElem.screenshot({ path: thumbPngPath });
      await thumbPage.close();
      console.log('✅ excursionlens-devpost-thumbnail.png rendered.');
    }

    // 3. Capture Real Application Screenshots
    const page = await browser.newPage({
      viewport: { width: 1280, height: 800 },
      deviceScaleFactor: 2,
    });

    console.log('Navigating to http://127.0.0.1:8000 for live app screenshots...');
    await page.goto('http://127.0.0.1:8000', { waitUntil: 'networkidle' });

    // Screenshot 1: 01_case_overview.png
    console.log('Capturing 01_case_overview.png...');
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '01_case_overview.png') });

    // Screenshot 2: 02_timeline_evidence.png
    console.log('Capturing 02_timeline_evidence.png...');
    const timelineElem = page.locator('.card').first();
    await timelineElem.screenshot({ path: path.join(SCREENSHOTS_DIR, '02_timeline_evidence.png') });

    // Trigger Investigation
    console.log('Triggering investigation for post-investigation screenshots...');
    const investBtn = page.getByRole('button', { name: /Investigate Excursion/i });
    await investBtn.click();
    await page.waitForSelector('text=Investigation complete', { timeout: 15000 });

    // Screenshot 3: 03_hypothesis_board.png
    console.log('Capturing 03_hypothesis_board.png...');
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '03_hypothesis_board.png') });

    // Trigger Counterfactual Replay
    console.log('Replaying counterfactual for 04_counterfactual.png...');
    const replayBtn = page.getByRole('button', { name: /Replay Counterfactual/i });
    await replayBtn.click();
    await page.waitForSelector('text=Simulation Completed', { timeout: 5000 });

    // Screenshot 4: 04_counterfactual.png
    console.log('Capturing 04_counterfactual.png...');
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '04_counterfactual.png') });

    // Open Review Packet Modal
    console.log('Opening Review Packet for 05_review_packet.png...');
    const reviewBtn = page.getByRole('button', { name: /Review Packet/i });
    await reviewBtn.click();
    await page.waitForSelector('text=ExcursionLens Quality Review Packet', { timeout: 5000 });

    // Screenshot 5: 05_review_packet.png
    console.log('Capturing 05_review_packet.png...');
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '05_review_packet.png') });

    console.log('🎉 All 5 product screenshots and graphic assets captured successfully!');
  } finally {
    await browser.close();
    server.kill();
  }
}

main().catch((err) => {
  console.error('Error capturing assets:', err);
  process.exit(1);
});
