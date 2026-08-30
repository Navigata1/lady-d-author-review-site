#!/usr/bin/env node
import { createServer } from "node:http";
import { readFile, stat, writeFile, mkdir } from "node:fs/promises";
import { createRequire } from "node:module";
import { extname, join, normalize, resolve } from "node:path";

const require = createRequire(import.meta.url);
const { chromium } = require(join(process.env.NODE_PATH, "playwright"));

const root = resolve(import.meta.dirname, "../..");
const evidencePath = join(root, "ops/mission/evidence/P4-G1-2026-08-30.json");
const screenshotDir = join(root, "tmp/finalization-release");
const port = 18792;

const contentTypes = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".md": "text/markdown; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".pdf": "application/pdf",
  ".zip": "application/zip",
};

const server = createServer(async (request, response) => {
  try {
    const requestPath = decodeURIComponent(new URL(request.url, `http://127.0.0.1:${port}`).pathname);
    const relative = requestPath === "/" ? "index.html" : requestPath.replace(/^\/+/, "");
    const path = normalize(join(root, relative));
    if (!path.startsWith(root)) throw new Error("path escape");
    const info = await stat(path);
    if (!info.isFile()) throw new Error("not a file");
    response.writeHead(200, { "content-type": contentTypes[extname(path)] || "application/octet-stream", "content-length": info.size });
    if (request.method === "HEAD") return response.end();
    response.end(await readFile(path));
  } catch {
    response.writeHead(404).end("Not found");
  }
});

await new Promise((accept) => server.listen(port, "127.0.0.1", accept));
await mkdir(screenshotDir, { recursive: true });
const browser = await chromium.launch({ headless: true, executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" });
const results = [];

try {
  for (const viewport of [{ width: 1440, height: 1100 }, { width: 390, height: 844 }]) {
    const page = await browser.newPage({ viewport });
    const errors = [];
    page.on("console", (message) => { if (message.type() === "error") errors.push(`console: ${message.text()}`); });
    page.on("pageerror", (error) => errors.push(`page: ${error.message}`));
    page.on("requestfailed", (request) => errors.push(`request: ${request.url()} ${request.failure()?.errorText || "failed"}`));
    const response = await page.goto(`http://127.0.0.1:${port}/lady-d-finalization-review.html`, { waitUntil: "networkidle" });
    const snapshot = await page.evaluate(() => ({
      title: document.title,
      h1: document.querySelector("h1")?.textContent?.trim(),
      bookRows: document.querySelectorAll(".book-row").length,
      coverChoices: document.querySelectorAll(".cover-choice").length,
      images: [...document.images].map((image) => ({ src: image.getAttribute("src"), complete: image.complete, width: image.naturalWidth })),
      overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
      links: [...document.querySelectorAll("a[href]")].map((link) => link.getAttribute("href")),
      hasFootprintsLock: document.body.textContent.includes("two complete walkers’ trails"),
    }));
    if (response?.status() !== 200) errors.push(`document status ${response?.status()}`);
    if (snapshot.bookRows !== 3) errors.push(`expected 3 book rows, got ${snapshot.bookRows}`);
    if (snapshot.coverChoices !== 3) errors.push(`expected 3 shortlisted covers, got ${snapshot.coverChoices}`);
    if (snapshot.overflow) errors.push("horizontal overflow");
    if (!snapshot.hasFootprintsLock) errors.push("Footprints composition lock missing");
    for (const image of snapshot.images) if (!image.complete || image.width < 1) errors.push(`image failed: ${image.src}`);

    const localLinks = [...new Set(snapshot.links.filter((href) => href && !href.startsWith("#") && !href.startsWith("http")))];
    const linkChecks = [];
    for (const href of localLinks) {
      const linkResponse = await page.request.head(new URL(href, page.url()).href);
      linkChecks.push({ href, status: linkResponse.status() });
      if (linkResponse.status() !== 200) errors.push(`link ${href} returned ${linkResponse.status()}`);
    }

    const label = `${viewport.width}x${viewport.height}`;
    await page.screenshot({ path: join(screenshotDir, `lady-d-finalization-${label}.png`), fullPage: true });
    results.push({ viewport, ...snapshot, linkChecks, errors, status: errors.length ? "FAIL" : "PASS" });
    await page.close();
  }

  const coverPage = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const coverResponse = await coverPage.goto(`http://127.0.0.1:${port}/lady-d-cover-decision-deck.html`, { waitUntil: "networkidle" });
  const coverCount = await coverPage.locator(".candidate").count();
  results.push({ page: "cover-decision-deck", statusCode: coverResponse?.status(), coverCount, status: coverResponse?.status() === 200 && coverCount === 10 ? "PASS" : "FAIL" });
  await coverPage.close();
} finally {
  await browser.close();
  server.close();
}

const status = results.every((item) => item.status === "PASS") ? "PASS" : "FAIL";
const report = { status, results };
await writeFile(evidencePath, JSON.stringify(report, null, 2) + "\n");
console.log(JSON.stringify(report, null, 2));
if (status !== "PASS") process.exit(1);
