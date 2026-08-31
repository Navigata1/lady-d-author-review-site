#!/usr/bin/env node

const { chromium } = require("playwright");
const fs = require("node:fs");
const path = require("node:path");

const base = process.env.BASE_URL || "http://127.0.0.1:8792";
const root = path.resolve(__dirname, "../..");
const outputDir = path.join(root, "output/pdf");
const downloads = path.join(root, "downloads/lady-d-finalization");
const publicDownloads = path.join(root, "public/downloads/lady-d-finalization");
for (const dir of [outputDir, downloads, publicDownloads]) fs.mkdirSync(dir, { recursive: true });

function mirror(source, destinations) {
  for (const destination of destinations) fs.copyFileSync(source, destination);
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const proposal = await browser.newPage();
    await proposal.goto(`${base}/susan-damon-publishing-proposal.html`, { waitUntil: "networkidle" });
    await proposal.emulateMedia({ media: "print" });
    const proposalPdf = path.join(root, "susan-damon-publishing-proposal.pdf");
    await proposal.pdf({
      path: proposalPdf,
      format: "Letter",
      printBackground: true,
      preferCSSPageSize: true,
      margin: { top: "0", right: "0", bottom: "0", left: "0" },
    });
    mirror(proposalPdf, [
      path.join(root, "public/susan-damon-publishing-proposal.pdf"),
      path.join(root, "susan-damon-expanded-invoice.pdf"),
      path.join(root, "public/susan-damon-expanded-invoice.pdf"),
    ]);
    await proposal.close();

    const devotional = await browser.newPage();
    await devotional.goto(`${base}/lady-d-31-day-visual-devotional.html`, { waitUntil: "networkidle" });
    await devotional.emulateMedia({ media: "print" });
    const devotionalPdf = path.join(outputDir, "Lady-D-31-Day-Visual-Devotional-Print-Proof.pdf");
    await devotional.pdf({
      path: devotionalPdf,
      width: "6in",
      height: "9in",
      printBackground: true,
      preferCSSPageSize: true,
      margin: { top: "0", right: "0", bottom: "0", left: "0" },
    });
    mirror(devotionalPdf, [
      path.join(downloads, "Lady-D-31-Day-Visual-Devotional-Print-Proof.pdf"),
      path.join(publicDownloads, "Lady-D-31-Day-Visual-Devotional-Print-Proof.pdf"),
    ]);
    await devotional.close();
    console.log(JSON.stringify({ proposalPdf, devotionalPdf }, null, 2));
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error.stack || error);
  process.exit(1);
});
