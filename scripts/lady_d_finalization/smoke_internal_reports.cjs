#!/usr/bin/env node

const { chromium } = require("playwright");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "../..");
const reportDir = path.resolve(root, "../_internal/2026-08-31");
const proofDir = path.join(root, "quality/visual-proof/internal-reports");
fs.mkdirSync(proofDir, { recursive: true });

const reports = [
  ["state", "Lady-D-State-of-the-Union-v2-2026-08-31.html"],
  ["plan", "Lady-D-Plan-of-Attack-v2-2026-08-31.html"],
];

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    for (const [name, filename] of reports) {
      for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
        const page = await browser.newPage({ viewport });
        const errors = [];
        page.on("console", (message) => message.type() === "error" && errors.push(message.text()));
        page.on("pageerror", (error) => errors.push(error.message));
        await page.goto(`file://${path.join(reportDir, filename)}`, { waitUntil: "networkidle" });
        const result = await page.evaluate(() => ({
          overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
          stories: document.querySelectorAll("[data-story]").length,
          brokenImages: [...document.images].filter((image) => !image.complete || image.naturalWidth === 0).length,
        }));
        if (result.overflow || result.stories < 5 || result.brokenImages || errors.length) {
          throw new Error(`${name}/${viewport.width} failed: ${JSON.stringify({ result, errors })}`);
        }
        await page.screenshot({ path: path.join(proofDir, `${name}-${viewport.width}.png`), fullPage: true });
        await page.close();
      }
    }
    console.log(JSON.stringify({ status: "PASS", reports: 2, viewports: [1440, 390] }, null, 2));
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error.stack || error);
  process.exit(1);
});
