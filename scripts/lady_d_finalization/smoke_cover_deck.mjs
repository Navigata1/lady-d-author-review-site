import fs from 'node:fs';
import { createRequire } from 'node:module';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const { chromium } = require(path.join(process.env.NODE_PATH, 'playwright'));
const root = path.resolve(here, '../..');
const publicDir = path.join(root, 'public');
const server = http.createServer((request, response) => {
  const requestPath = decodeURIComponent(new URL(request.url, 'http://127.0.0.1').pathname);
  const relative = requestPath === '/' ? 'lady-d-cover-decision-deck.html' : requestPath.replace(/^\/+/, '');
  const candidate = path.resolve(publicDir, relative);
  if (!candidate.startsWith(publicDir + path.sep) || !fs.existsSync(candidate) || !fs.statSync(candidate).isFile()) {
    response.writeHead(404).end('Not found');
    return;
  }
  const type = candidate.endsWith('.html') ? 'text/html' : candidate.endsWith('.png') ? 'image/png' : 'application/octet-stream';
  response.writeHead(200, { 'content-type': type });
  fs.createReadStream(candidate).pipe(response);
});
await new Promise(resolve => server.listen(18791, '127.0.0.1', resolve));
const target = 'http://127.0.0.1:18791/lady-d-cover-decision-deck.html';
const browser = await chromium.launch({ headless: true, executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' });
const failures = [];
const evidence = { schema: 'lady-d.cover-deck-smoke/v1', target, gate: 'PASS', viewports: [] };
const screenshotDir = path.join(root, 'tmp/covers/finalization');
fs.mkdirSync(screenshotDir, { recursive: true });

for (const viewport of [{ width: 1440, height: 1100 }, { width: 390, height: 844 }]) {
  const page = await browser.newPage({ viewport });
  const errors = [];
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(target, { waitUntil: 'load' });
  const result = await page.evaluate(() => ({
    candidates: document.querySelectorAll('.candidate').length,
    visible: [...document.querySelectorAll('.candidate')].filter(node => !node.hidden).length,
    shortlist: document.querySelectorAll('.select.chosen').length,
    overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
    images: [...document.querySelectorAll('.cover')].filter(node => getComputedStyle(node).backgroundImage !== 'none').length,
  }));
  await page.locator('[data-filter="2"]').click();
  result.volumeTwoVisible = await page.locator('.candidate:not([hidden])').count();
  await page.locator('[data-filter="all"]').click();
  await page.screenshot({
    path: path.join(screenshotDir, `cover-deck-${viewport.width}.png`),
    fullPage: true,
  });
  result.errors = errors;
  evidence.viewports.push({ viewport, ...result });
  if (result.candidates !== 10 || result.visible !== 10 || result.shortlist !== 3 || result.overflow || result.images !== 10 || result.volumeTwoVisible !== 4 || errors.length) {
    failures.push({ viewport, result });
  }
  await page.close();
}

await browser.close();
await new Promise(resolve => server.close(resolve));
evidence.gate = failures.length ? 'FAIL' : 'PASS';
evidence.failures = failures;
const output = path.join(root, 'ops/mission/evidence/P3-G2-2026-08-30.json');
fs.mkdirSync(path.dirname(output), { recursive: true });
fs.writeFileSync(output, JSON.stringify(evidence, null, 2) + '\n');
console.log(`Cover deck smoke: ${evidence.gate}`);
console.log(JSON.stringify(evidence.viewports, null, 2));
if (failures.length) process.exit(1);
