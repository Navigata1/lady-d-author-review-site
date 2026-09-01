#!/usr/bin/env node

const { chromium } = require("playwright");
const fs = require("node:fs");
const path = require("node:path");

const base = process.env.BASE_URL || "http://127.0.0.1:8793";
const root = path.resolve(__dirname, "../..");
const quality = path.join(root, "quality/31-day-visual-journal-v2");
const pagesDir = path.join(quality, "composed-pages");
fs.mkdirSync(pagesDir, { recursive: true });

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function inspect(viewport, label, capturePages = false) {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport, deviceScaleFactor: 1 });
  const errors = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(`console: ${message.text()}`);
  });
  page.on("pageerror", (error) => errors.push(`page: ${error.message}`));
  try {
    const response = await page.goto(`${base}/lady-d-31-day-visual-journal.html`, { waitUntil: "networkidle" });
    assert(response && response.ok(), "visual journal did not return 2xx");
    await page.evaluate(() => document.fonts.ready);
    const diagnostics = await page.evaluate(() => {
      const pages = [...document.querySelectorAll(".journal-page")];
      return {
        pageCount: pages.length,
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
        brokenImages: [...document.images].filter((image) => !image.complete || image.naturalWidth === 0).map((image) => image.src),
        proofFlags: document.querySelectorAll(".proof-flag").length,
        pages: pages.map((leaf) => {
          const copy = leaf.querySelector(".copy");
          const footer = leaf.querySelector("footer");
          const leafRect = leaf.getBoundingClientRect();
          const copyRect = copy.getBoundingClientRect();
          const footerRect = footer.getBoundingClientRect();
          return {
            day: Number(leaf.dataset.day),
            width: Math.round(leafRect.width),
            height: Math.round(leafRect.height),
            copyInside: copyRect.left >= leafRect.left - 1 && copyRect.right <= leafRect.right + 1 && copyRect.top >= leafRect.top - 1 && copyRect.bottom <= leafRect.bottom + 1,
            footerClear: copyRect.bottom <= footerRect.top - 2 || copyRect.top >= footerRect.bottom + 2,
            copyOverflow: copy.scrollWidth > copy.clientWidth + 1 || copy.scrollHeight > copy.clientHeight + 1,
            title: copy.querySelector("h2")?.textContent.trim(),
          };
        }),
      };
    });
    assert(diagnostics.pageCount === 31, `expected 31 pages, found ${diagnostics.pageCount}`);
    assert(diagnostics.scrollWidth <= diagnostics.clientWidth + 1, `${label} layout has horizontal overflow`);
    assert(diagnostics.brokenImages.length === 0, `${label} has broken images: ${diagnostics.brokenImages.join(", ")}`);
    assert(diagnostics.proofFlags === 0, `${label} still contains pending-scene proof flags`);
    assert(errors.length === 0, `${label} emitted errors: ${errors.join(" | ")}`);
    const titles = new Set();
    for (const record of diagnostics.pages) {
      assert(record.copyInside, `day ${record.day} copy leaves the page at ${label}`);
      assert(record.footerClear, `day ${record.day} copy overlaps the footer at ${label}`);
      assert(!record.copyOverflow, `day ${record.day} copy overflows its container at ${label}`);
      assert(record.title, `day ${record.day} has no visible title at ${label}`);
      titles.add(record.title);
    }
    assert(titles.size === 31, `${label} does not expose 31 distinct titles`);

    await page.screenshot({ path: path.join(quality, `journal-${label}.png`), fullPage: false });
    if (capturePages) {
      const leaves = page.locator(".journal-page");
      for (let index = 0; index < 31; index += 1) {
        await leaves.nth(index).screenshot({ path: path.join(pagesDir, `day-${String(index + 1).padStart(2, "0")}.png`) });
      }
    }
    return diagnostics;
  } finally {
    await browser.close();
  }
}

(async () => {
  const desktop = await inspect({ width: 1440, height: 1000 }, "desktop", true);
  const mobile = await inspect({ width: 390, height: 844 }, "mobile", false);
  const report = {
    schema: "idc.lady_d_31_day_visual_journal_browser_gauntlet/v2",
    status: "PASS",
    base,
    pageCount: desktop.pageCount,
    desktop: { viewport: [1440, 1000], pageSize: [desktop.pages[0].width, desktop.pages[0].height] },
    mobile: { viewport: [390, 844], pageSize: [mobile.pages[0].width, mobile.pages[0].height] },
    composedPageScreenshots: 31,
    consoleErrors: 0,
    brokenImages: 0,
    overflows: 0,
  };
  fs.writeFileSync(path.join(quality, "browser-gauntlet.json"), `${JSON.stringify(report, null, 2)}\n`);
  console.log(JSON.stringify(report, null, 2));
})().catch((error) => {
  console.error(error.stack || error);
  process.exit(1);
});
