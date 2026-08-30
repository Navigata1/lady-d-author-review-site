#!/usr/bin/env python3
"""Render the six Lady D 6x9 interiors with headless Chrome."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HTML_DIR = ROOT / "public/downloads/lady-d-finalization"
PDF_DIR = ROOT / "output/pdf"
PUBLIC_DIR = ROOT / "public/downloads/lady-d-finalization"
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")

JOBS = [
    (
        "volume-1-surrendering-to-gods-love-polished-devotional.html",
        "Lady-D-Volume-1-Surrendering-to-Gods-Love-Polished-6x9.pdf",
    ),
    (
        "volume-1-surrendering-to-gods-love-polished-companion-journal.html",
        "Lady-D-Volume-1-Surrendering-to-Gods-Love-Companion-Journal-Deep-Dive-6x9.pdf",
    ),
    (
        "volume-2-walking-with-jesus-polished-devotional.html",
        "Lady-D-Volume-2-Walking-with-Jesus-Polished-6x9.pdf",
    ),
    (
        "volume-2-walking-with-jesus-polished-companion-journal.html",
        "Lady-D-Volume-2-Walking-with-Jesus-Companion-Journal-Deep-Dive-6x9.pdf",
    ),
    (
        "volume-3-filled-with-the-holy-spirit-polished-devotional.html",
        "Lady-D-Volume-3-Filled-with-the-Holy-Spirit-Polished-6x9.pdf",
    ),
    (
        "volume-3-filled-with-the-holy-spirit-polished-companion-journal.html",
        "Lady-D-Volume-3-Filled-with-the-Holy-Spirit-Companion-Journal-Deep-Dive-6x9.pdf",
    ),
]


def main() -> None:
    if not CHROME.exists():
        raise SystemExit(f"Chrome not found at {CHROME}")
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    rendered: list[dict[str, object]] = []

    for html_name, pdf_name in JOBS:
        with tempfile.TemporaryDirectory(prefix="lady-d-chrome-") as profile:
            html_path = HTML_DIR / html_name
            pdf_path = PDF_DIR / pdf_name
            if not html_path.exists():
                raise SystemExit(f"missing HTML interior: {html_path}")
            command = [
                str(CHROME),
                "--headless=new",
                "--disable-gpu",
                "--disable-extensions",
                "--no-pdf-header-footer",
                "--run-all-compositor-stages-before-draw",
                f"--user-data-dir={profile}",
                f"--print-to-pdf={pdf_path}",
                html_path.resolve().as_uri(),
            ]
            pdf_path.unlink(missing_ok=True)
            process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            expected_pages = 420 if "journal" in html_name else 754
            stable_size = -1
            stable_checks = 0
            deadline = time.monotonic() + 240
            valid = False
            while time.monotonic() < deadline:
                time.sleep(2)
                if not pdf_path.exists() or pdf_path.stat().st_size < 100_000:
                    if process.poll() is not None:
                        break
                    continue
                current_size = pdf_path.stat().st_size
                if current_size == stable_size:
                    stable_checks += 1
                else:
                    stable_size = current_size
                    stable_checks = 0
                if stable_checks < 3:
                    continue
                info = subprocess.run(
                    ["pdfinfo", str(pdf_path)],
                    capture_output=True,
                    text=True,
                )
                if info.returncode == 0 and f"Pages:           {expected_pages}" in info.stdout:
                    valid = True
                    break

            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)

            if not valid:
                raise SystemExit(
                    f"Chrome did not produce a stable {expected_pages}-page PDF for {html_name}"
                )

            public_path = PUBLIC_DIR / pdf_name
            shutil.copy2(pdf_path, public_path)
            rendered.append(
                {
                    "source": str(html_path.relative_to(ROOT)),
                    "pdf": str(pdf_path.relative_to(ROOT)),
                    "public_copy": str(public_path.relative_to(ROOT)),
                    "bytes": pdf_path.stat().st_size,
                }
            )

    print(json.dumps({"rendered": rendered}, indent=2))


if __name__ == "__main__":
    main()
