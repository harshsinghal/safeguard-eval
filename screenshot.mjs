import puppeteer from 'puppeteer-core';
import { mkdir } from 'fs/promises';
import { existsSync } from 'fs';

const BASE_URL = 'http://localhost:5001';
const CHROME = '/usr/bin/google-chrome';
const OUT_DIR = 'docs';

async function wait(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function main() {
  await mkdir(OUT_DIR, { recursive: true });

  const browser = await puppeteer.launch({
    executablePath: CHROME,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
    headless: true,
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1400, height: 860 });

  // ── 1. Main UI on load ──────────────────────────────────────────────────
  await page.goto(BASE_URL, { waitUntil: 'networkidle2' });
  await page.waitForSelector('.policy-card');
  await wait(300);
  await page.screenshot({ path: `${OUT_DIR}/01-main.png` });
  console.log('✓ 01-main.png');

  // ── 2. Policy selected ──────────────────────────────────────────────────
  // Click deity_nuanced (more interesting than nsfw_strict)
  const cards = await page.$$('.policy-card');
  for (const card of cards) {
    const name = await card.$eval('.policy-name', el => el.textContent);
    if (name.includes('deity')) {
      await card.click();
      break;
    }
  }
  await wait(500);
  await page.screenshot({ path: `${OUT_DIR}/02-policy-selected.png` });
  console.log('✓ 02-policy-selected.png');

  // ── 3. Prompt entered ───────────────────────────────────────────────────
  const prompt = 'A traditional oil painting of Lord Shiva in the Himalayan mountains, depicted in a classical Indian art style with symbolic attributes';
  await page.type('#contentInput', prompt);
  await wait(200);
  await page.screenshot({ path: `${OUT_DIR}/03-prompt-entered.png` });
  console.log('✓ 03-prompt-entered.png');

  // ── 4. Evaluation result ────────────────────────────────────────────────
  await page.click('#evaluateBtn');
  await page.waitForSelector('.result-container.show', { timeout: 30000 });
  await wait(400);
  // Scroll result into view and screenshot full page
  await page.evaluate(() => {
    document.getElementById('resultContainer').scrollIntoView({ behavior: 'instant' });
  });
  await wait(200);
  await page.screenshot({ path: `${OUT_DIR}/04-evaluation-result.png` });
  console.log('✓ 04-evaluation-result.png');

  // ── 5. nsfw_strict policy with unsafe prompt ────────────────────────────
  await page.evaluate(() => {
    document.getElementById('contentInput').value = '';
    document.getElementById('resultContainer').classList.remove('show');
    window.scrollTo(0, 0);
  });

  // Select nsfw_strict
  const cards2 = await page.$$('.policy-card');
  for (const card of cards2) {
    const name = await card.$eval('.policy-name', el => el.textContent);
    if (name.includes('nsfw_strict')) {
      await card.click();
      break;
    }
  }
  await wait(400);

  await page.type('#contentInput', 'A scenic mountain landscape at golden hour, peaceful valley with wildflowers');
  await wait(200);
  await page.click('#evaluateBtn');
  await page.waitForSelector('.result-container.show', { timeout: 30000 });
  await wait(400);
  await page.evaluate(() => {
    document.getElementById('resultContainer').scrollIntoView({ behavior: 'instant' });
  });
  await wait(200);
  await page.screenshot({ path: `${OUT_DIR}/05-safe-result.png` });
  console.log('✓ 05-safe-result.png');

  await browser.close();
  console.log(`\nScreenshots saved to ./${OUT_DIR}/`);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
