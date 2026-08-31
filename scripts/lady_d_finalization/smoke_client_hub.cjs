#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');
const { chromium } = require('playwright');

const root = path.resolve(__dirname, '..', '..');
const pagePath = path.join(root, 'susan-damon-hub.html');
const captureDir = path.join(root, 'tmp', 'hub-revamp');
const stripeUrl = 'https://buy.stripe.com/fZu28t5WpchE73EbnA0VO0a';
const forbidden = [
  'Enhanced State',
  'Plan of Attack',
  'Judge PASS',
  'Auditor PASS',
  'command hub',
  'independent manuscript',
  'retired checkout',
  'stripe-payment-link-pending-1400.html',
];

function localLinks(html) {
  const matches = [...html.matchAll(/href="([^"]+)"/g)].map((match) => match[1]);
  return matches.filter((href) => !href.startsWith('#') && !/^(https?:|mailto:|tel:)/.test(href));
}

async function inspect(browser, name, viewport) {
  const errors = [];
  const page = await browser.newPage({ viewport, deviceScaleFactor: 1 });
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(`console: ${message.text()}`);
  });
  page.on('pageerror', (error) => errors.push(`page: ${error.message}`));
  page.on('requestfailed', (request) => errors.push(`request: ${request.url()}`));
  await page.goto(pathToFileURL(pagePath).href, { waitUntil: 'load' });
  await page.screenshot({ path: path.join(captureDir, `hub-${name}.png`), fullPage: true });
  const result = await page.evaluate(() => ({
    width: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
    height: document.documentElement.scrollHeight,
    books: document.querySelectorAll('.book-card').length,
    brokenImages: [...document.images].filter((image) => !image.complete || image.naturalWidth === 0).map((image) => image.src),
    pendingLinks: document.querySelectorAll('a[href*="stripe-payment-link-pending"]').length,
    stripeLinks: [...document.querySelectorAll('a[href^="https://buy.stripe.com/"]')].map((link) => link.href),
    pendingCopy: document.body.textContent.includes('Secure payment link being confirmed'),
    h1: document.querySelector('h1')?.textContent.trim(),
  }));
  await page.close();
  return { name, ...result, errors };
}

(async () => {
  fs.mkdirSync(captureDir, { recursive: true });
  const html = fs.readFileSync(pagePath, 'utf8');
  const forbiddenHits = forbidden.filter((phrase) => html.toLowerCase().includes(phrase.toLowerCase()));
  const missingLinks = localLinks(html).filter((href) => {
    const clean = decodeURIComponent(href.split('#')[0].split('?')[0]);
    return !fs.existsSync(path.resolve(root, clean));
  });
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  });
  const views = [];
  views.push(await inspect(browser, 'desktop', { width: 1440, height: 1000 }));
  views.push(await inspect(browser, 'mobile', { width: 390, height: 844 }));
  await browser.close();

  const failures = [];
  if (forbiddenHits.length) failures.push(`forbidden copy: ${forbiddenHits.join(', ')}`);
  if (missingLinks.length) failures.push(`missing links: ${missingLinks.join(', ')}`);
  for (const view of views) {
    if (view.width > view.clientWidth) failures.push(`${view.name}: horizontal overflow ${view.width}/${view.clientWidth}`);
    if (view.books !== 3) failures.push(`${view.name}: expected 3 books, got ${view.books}`);
    if (view.brokenImages.length) failures.push(`${view.name}: broken images ${view.brokenImages.join(', ')}`);
    if (view.pendingLinks !== 0) failures.push(`${view.name}: retired payment placeholder is linked`);
    if (view.pendingCopy) failures.push(`${view.name}: pending payment copy remains`);
    if (view.stripeLinks.length !== 1 || view.stripeLinks[0] !== stripeUrl) failures.push(`${view.name}: expected one verified Stripe link`);
    if (view.errors.length) failures.push(`${view.name}: browser errors ${view.errors.join(' | ')}`);
  }
  const report = { status: failures.length ? 'FAIL' : 'PASS', forbiddenHits, missingLinks, views, failures };
  process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
  process.exitCode = failures.length ? 1 : 0;
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
