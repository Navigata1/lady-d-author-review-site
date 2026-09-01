#!/usr/bin/env node

const { chromium } = require("playwright");
const fs = require("node:fs");
const path = require("node:path");

const base = process.env.BASE_URL || "http://127.0.0.1:8793";
const root = path.resolve(__dirname, "../..");
const output = path.join(root, "output/pdf/Lady-D-Thirty-One-Mornings-of-Light-Visual-Journal-6x9.pdf");
const mirrors = [
  path.join(root, "downloads/lady-d-finalization/Lady-D-Thirty-One-Mornings-of-Light-Visual-Journal-6x9.pdf"),
  path.join(root, "public/downloads/lady-d-finalization/Lady-D-Thirty-One-Mornings-of-Light-Visual-Journal-6x9.pdf"),
];
for (const directory of [path.dirname(output), ...mirrors.map(path.dirname)]) fs.mkdirSync(directory, { recursive: true });

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    const response = await page.goto(`${base}/lady-d-31-day-visual-journal.html`, { waitUntil: "networkidle" });
    if (!response || !response.ok()) throw new Error("visual journal route did not return 2xx");
    await page.evaluate(() => document.fonts.ready);
    await page.emulateMedia({ media: "print" });
    await page.pdf({
      path: output,
      width: "6in",
      height: "9in",
      printBackground: true,
      preferCSSPageSize: true,
      margin: { top: "0", right: "0", bottom: "0", left: "0" },
    });
    for (const mirror of mirrors) fs.copyFileSync(output, mirror);
    console.log(JSON.stringify({ status: "created", output, mirrors, bytes: fs.statSync(output).size }, null, 2));
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error.stack || error);
  process.exit(1);
});
