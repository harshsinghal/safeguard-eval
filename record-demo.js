/**
 * record-demo.js
 *
 * Records a demo animation of the OSS-Safeguard Policy Tester app
 * showing the copyright_characters policy being used to evaluate a
 * prompt that requests a copyrighted character image.
 *
 * Prerequisites:
 *   npm install          # installs puppeteer-core
 *   python app.py &      # Flask server must be running on :5001
 *
 * Usage:
 *   node record-demo.js
 *
 * Output:
 *   screenshots/frame-*.png  — raw frames
 *   demo.gif                 — final animated GIF (via ffmpeg)
 */

const puppeteer = require('puppeteer-core');
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const APP_URL = 'http://localhost:5001';
const CHROME_PATH = '/usr/bin/google-chrome';
const FRAMES_DIR = path.join(__dirname, 'screenshots', 'frames');
const OUTPUT_GIF = path.join(__dirname, 'demo.gif');
const VIEWPORT = { width: 1280, height: 900 };

// Typing helper — types one character at a time for a realistic feel
async function typeSlowly(page, selector, text, delay = 45) {
  await page.click(selector, { clickCount: 3 }); // select all first
  for (const char of text) {
    await page.type(selector, char, { delay });
  }
}

// Sleep helper
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Capture a frame (or several identical frames to add dwell time)
let frameIdx = 0;
async function capture(page, dwellMs = 600) {
  const framesPerDwell = Math.max(1, Math.round(dwellMs / 80)); // ~12 fps
  const framePath = path.join(FRAMES_DIR, `frame-${String(frameIdx).padStart(4, '0')}.png`);
  await page.screenshot({ path: framePath });
  // Duplicate the frame to hold the pause
  for (let i = 1; i < framesPerDwell; i++) {
    const dup = path.join(FRAMES_DIR, `frame-${String(frameIdx + i).padStart(4, '0')}.png`);
    fs.copyFileSync(framePath, dup);
  }
  frameIdx += framesPerDwell;
}

// Smooth scroll to an element
async function scrollTo(page, selector) {
  await page.$eval(selector, (el) => el.scrollIntoView({ behavior: 'smooth', block: 'center' }));
  await sleep(400);
}

async function main() {
  // Prepare frames directory
  if (fs.existsSync(FRAMES_DIR)) {
    fs.readdirSync(FRAMES_DIR).forEach((f) => fs.unlinkSync(path.join(FRAMES_DIR, f)));
  } else {
    fs.mkdirSync(FRAMES_DIR, { recursive: true });
  }

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const page = await browser.newPage();
  await page.setViewport(VIEWPORT);

  // ── Step 1: Load the app ──────────────────────────────────────────────────
  console.log('Loading app...');
  await page.goto(APP_URL, { waitUntil: 'networkidle2' });
  await sleep(800);
  await capture(page, 1200); // hold on initial page load

  // ── Step 2: Wait for policies to render, then highlight copyright card ───
  console.log('Selecting copyright_characters policy...');
  await page.waitForSelector('.policy-card', { timeout: 8000 });
  await capture(page, 800);

  // Click the copyright_characters policy card
  const policyClicked = await page.evaluate(() => {
    const cards = Array.from(document.querySelectorAll('.policy-card'));
    const target = cards.find((c) => c.textContent.toLowerCase().includes('copyright'));
    if (target) { target.click(); return true; }
    return false;
  });

  if (!policyClicked) {
    console.error('Could not find copyright_characters policy card');
    await browser.close();
    process.exit(1);
  }

  await sleep(600);
  await capture(page, 1000);

  // ── Step 3: Scroll down to the policy preview ────────────────────────────
  await page.evaluate(() => {
    const preview = document.getElementById('policyPreview');
    if (preview) preview.scrollIntoView({ behavior: 'smooth', block: 'center' });
  });
  await sleep(500);
  await capture(page, 1200);

  // ── Step 4: Type the copyright prompt ────────────────────────────────────
  console.log('Typing the prompt...');
  await scrollTo(page, '#contentInput');
  await capture(page, 600);

  const prompt =
    'Generate a realistic image of Spider-Man swinging through New York City at sunset, ' +
    'wearing his classic red and blue Marvel Comics costume with the iconic web pattern.';

  // Type character by character for visual effect
  await page.click('#contentInput');
  for (const char of prompt) {
    await page.type('#contentInput', char, { delay: 28 });
    // Capture a frame every ~8 characters so the typing is visible
    if (frameIdx % 8 === 0) {
      const framePath = path.join(FRAMES_DIR, `frame-${String(frameIdx).padStart(4, '0')}.png`);
      await page.screenshot({ path: framePath });
      frameIdx++;
    }
  }
  await capture(page, 1000);

  // ── Step 5: Click "Evaluate Content" ─────────────────────────────────────
  console.log('Clicking Evaluate...');
  await page.waitForSelector('#evaluateBtn:not([disabled])', { timeout: 5000 });
  await page.click('#evaluateBtn');
  await capture(page, 600);

  // Show the loading spinner
  await scrollTo(page, '#evaluateLoading');
  await capture(page, 800);

  // Wait for the result container to appear (API call)
  console.log('Waiting for evaluation result...');
  await page.waitForSelector('#resultContainer.show', { timeout: 30000 });
  await sleep(600);
  await scrollTo(page, '#resultContainer');
  await capture(page, 2500); // hold on the result

  // ── Step 6: Final wide shot of result ────────────────────────────────────
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await sleep(500);
  await capture(page, 1200);

  await browser.close();

  // ── Assemble GIF with ffmpeg ──────────────────────────────────────────────
  console.log(`\nAssembling ${frameIdx} frames into GIF...`);
  const ffmpegCmd = [
    'ffmpeg -y',
    `-framerate 12`,
    `-i "${FRAMES_DIR}/frame-%04d.png"`,
    // Two-pass palette for crisp colours
    `-vf "fps=12,scale=1280:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer"`,
    `"${OUTPUT_GIF}"`,
  ].join(' ');

  try {
    execSync(ffmpegCmd, { stdio: 'inherit' });
    console.log(`\nDone! GIF saved to: ${OUTPUT_GIF}`);
  } catch (err) {
    console.error('ffmpeg failed:', err.message);
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
