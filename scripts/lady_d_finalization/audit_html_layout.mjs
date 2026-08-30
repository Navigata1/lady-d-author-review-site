#!/usr/bin/env node

import fs from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import { pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require(path.join(process.env.NODE_PATH, "playwright"));

const root = path.resolve(import.meta.dirname, "../..");
const htmlDir = path.join(root, "public/downloads/lady-d-finalization");
const files = fs.readdirSync(htmlDir).filter((name) => name.endsWith(".html")).sort();
const browser = await chromium.launch({
  executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  headless: true,
});

const results = {};
let failed = false;

for (const filename of files) {
  const page = await browser.newPage({ viewport: { width: 900, height: 1200 } });
  const consoleErrors = [];
  const pageErrors = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await page.goto(pathToFileURL(path.join(htmlDir, filename)).href, { waitUntil: "load" });
  await page.evaluate(async () => {
    if (document.fonts?.ready) await document.fonts.ready;
  });

  const layout = await page.evaluate(() => {
    const leaves = [...document.querySelectorAll(".leaf")];
    const overflow = [];
    const dimensions = new Set();
    for (const [index, leaf] of leaves.entries()) {
      const rect = leaf.getBoundingClientRect();
      dimensions.add(`${Math.round(rect.width)}x${Math.round(rect.height)}`);
      const flow = leaf.querySelector(".flow");
      if (leaf.scrollHeight > leaf.clientHeight + 1 || leaf.scrollWidth > leaf.clientWidth + 1) {
        overflow.push({ page: index + 1, kind: "leaf", scrollHeight: leaf.scrollHeight, clientHeight: leaf.clientHeight });
      }
      if (flow && (flow.scrollHeight > flow.clientHeight + 2 || flow.scrollWidth > flow.clientWidth + 2)) {
        overflow.push({ page: index + 1, kind: "flow", scrollHeight: flow.scrollHeight, clientHeight: flow.clientHeight });
      }
    }
    return { pageCount: leaves.length, dimensions: [...dimensions], overflow };
  });
  if (layout.overflow.length || pageErrors.length) failed = true;
  results[filename] = { ...layout, consoleErrors, pageErrors };
  await page.close();
}

await browser.close();
process.stdout.write(`${JSON.stringify({ status: failed ? "failed" : "passed", files: results }, null, 2)}\n`);
process.exitCode = failed ? 1 : 0;
