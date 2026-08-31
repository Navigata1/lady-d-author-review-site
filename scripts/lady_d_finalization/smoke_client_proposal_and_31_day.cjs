#!/usr/bin/env node

const { chromium } = require("playwright");
const fs = require("node:fs");
const path = require("node:path");

const base = process.env.BASE_URL || "http://127.0.0.1:8792";
const root = path.resolve(__dirname, "../..");
const evidenceDir = path.join(root, "quality/visual-proof/31-day");
fs.mkdirSync(evidenceDir, { recursive: true });

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function inspectPage(page, route, viewport, name) {
  const errors = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(`console: ${message.text()}`);
  });
  page.on("pageerror", (error) => errors.push(`page: ${error.message}`));
  const response = await page.goto(`${base}/${route}`, { waitUntil: "networkidle" });
  assert(response && response.ok(), `${route} did not return 2xx`);
  await page.setViewportSize(viewport);
  await page.waitForTimeout(500);
  const layout = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
    brokenImages: [...document.images].filter((image) => !image.complete || image.naturalWidth === 0).map((image) => image.src),
  }));
  assert(layout.scrollWidth <= layout.clientWidth + 1, `${route} has horizontal overflow at ${viewport.width}px`);
  assert(layout.brokenImages.length === 0, `${route} has broken images: ${layout.brokenImages.join(", ")}`);
  assert(errors.length === 0, `${route} emitted errors: ${errors.join(" | ")}`);
  await page.screenshot({ path: path.join(evidenceDir, `${name}-${viewport.width}.png`), fullPage: route !== "lady-d-31-day-motion.html" });
  return layout;
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
      const hub = await browser.newPage({ viewport });
      await inspectPage(hub, "susan-damon-hub.html", viewport, "hub");
      assert((await hub.locator("#visual").count()) === 1, "hub is missing the 31-day visual lane");
      assert((await hub.locator('a[href="lady-d-31-day-motion.html"]').count()) === 1, "hub is missing the motion edition link");
      assert((await hub.locator('a[href$="Lady-D-31-Day-Visual-Devotional-Production-Proof-2026-08-31.zip"]').count()) === 1, "hub is missing the portable 31-day package");
      assert((await hub.locator('a[href="https://buy.stripe.com/fZu28t5WpchE73EbnA0VO0a"]').count()) === 1, "hub is missing the reconciled Stripe checkout");
      await hub.close();

      const proposal = await browser.newPage({ viewport });
      await inspectPage(proposal, "susan-damon-publishing-proposal.html", viewport, "proposal");
      assert((await proposal.locator(".proposal-page").count()) === 8, "proposal is not eight pages");
      assert((await proposal.locator(".cover img").count()) === 3, "proposal does not show three luminous covers");
      assert((await proposal.locator('a[href="https://buy.stripe.com/fZu28t5WpchE73EbnA0VO0a"]').count()) >= 3, "proposal is missing the reconciled Stripe link");
      const proposalText = await proposal.locator("body").innerText();
      assert(!proposalText.includes("Enhanced State"), "proposal still exposes the old internal State link");
      assert(!proposalText.includes("Enhanced Plan"), "proposal still exposes the old internal Plan link");
      await proposal.close();

      const print = await browser.newPage({ viewport });
      await inspectPage(print, "lady-d-31-day-visual-devotional.html", viewport, "print-proof");
      assert((await print.locator(".leaf").count()) === 95, "31-day print proof should contain 95 intentional leaves");
      assert((await print.locator(".image-leaf").count()) === 31, "31-day print proof is missing visual leaves");
      assert((await print.locator(".reading-leaf").count()) === 31, "31-day print proof is missing reading leaves");
      assert((await print.locator(".journal-leaf").count()) === 31, "31-day print proof is missing carry-it-with-you leaves");
      assert((await print.locator("body").innerText()).includes("Ephesians 3:19"), "print proof is missing the Day 31 culmination");
      await print.close();

      const motion = await browser.newPage({ viewport });
      await inspectPage(motion, "lady-d-31-day-motion.html", viewport, "motion");
      assert((await motion.locator("#dayCount").innerText()).trim() === "1 / 31", "motion reader did not open on Day 1");
      await motion.locator("#next").click();
      assert((await motion.locator("#dayCount").innerText()).trim() === "2 / 31", "motion reader next control failed");
      await motion.locator("#read").click();
      assert(await motion.locator("#reader").evaluate((element) => element.classList.contains("open")), "motion reader drawer did not open");
      assert((await motion.locator("#readerBody p").count()) === 4, "motion reader does not show the four-paragraph devotional");
      const canvas = await motion.locator("#scene").boundingBox();
      assert(canvas && canvas.width >= viewport.width - 2 && canvas.height >= viewport.height - 2, "WebGL canvas is not full bleed");
      await motion.locator("#scene").screenshot({ path: path.join(evidenceDir, `motion-canvas-${viewport.width}.png`) });
      await motion.close();

      const review = await browser.newPage({ viewport });
      await inspectPage(review, "lady-d-31-day-scene-review.html", viewport, "scene-review");
      assert((await review.locator(".card").count()) === 31, "scene review console does not contain all 31 days");
      await review.locator('.decisions button[data-value="prompt-approved"]').first().click();
      assert((await review.locator(".status").first().innerText()).includes("prompt-approved"), "scene prompt decision did not persist in the UI");
      await review.close();
    }
    const report = { schema: "idc.lady_d_client_and_31_day_browser_gauntlet/v1", status: "PASS", base, viewports: [1440, 390], hub: "reconciled", proposalPages: 8, devotionalLeaves: 95, sceneCards: 31, webgl: "full-bleed" };
    fs.mkdirSync(path.join(root, "quality/31-day"), { recursive: true });
    fs.writeFileSync(path.join(root, "quality/31-day/browser-gauntlet.json"), `${JSON.stringify(report, null, 2)}\n`);
    console.log(JSON.stringify(report, null, 2));
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error.stack || error);
  process.exit(1);
});
