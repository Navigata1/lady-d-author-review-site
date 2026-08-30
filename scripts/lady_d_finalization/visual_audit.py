#!/usr/bin/env python3
"""Run browser overflow checks and render representative PDF pages for visual QA."""

from __future__ import annotations

import json
import os
import statistics
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[2]
PDF_DIR = ROOT / "output/pdf"
POLISHED_DIR = ROOT / "source/finalization/polished"
RENDER_DIR = ROOT / "tmp/pdfs/finalization"
EVIDENCE_PATH = ROOT / "ops/mission/evidence/P2-G2-2026-08-30.json"
NODE_PATH = "/Users/IDC2.5/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules"

PDF_NAMES = {
    1: (
        "Lady-D-Volume-1-Surrendering-to-Gods-Love-Polished-6x9.pdf",
        "Lady-D-Volume-1-Surrendering-to-Gods-Love-Companion-Journal-Deep-Dive-6x9.pdf",
    ),
    2: (
        "Lady-D-Volume-2-Walking-with-Jesus-Polished-6x9.pdf",
        "Lady-D-Volume-2-Walking-with-Jesus-Companion-Journal-Deep-Dive-6x9.pdf",
    ),
    3: (
        "Lady-D-Volume-3-Filled-with-the-Holy-Spirit-Polished-6x9.pdf",
        "Lady-D-Volume-3-Filled-with-the-Holy-Spirit-Companion-Journal-Deep-Dive-6x9.pdf",
    ),
}


def source_index_for_day(day: int) -> int:
    if day == 0:
        return 60
    return day if day < 60 else day + 1


def render_page(pdf: Path, page_number: int, output: Path) -> None:
    subprocess.run(
        [
            "pdftoppm",
            "-f",
            str(page_number),
            "-l",
            str(page_number),
            "-singlefile",
            "-r",
            "120",
            "-png",
            str(pdf),
            str(output.with_suffix("")),
        ],
        check=True,
        capture_output=True,
    )


def image_stats(path: Path) -> dict[str, object]:
    with Image.open(path) as image:
        gray = image.convert("L")
        values = list(gray.get_flattened_data())
        mean = statistics.fmean(values)
        stddev = statistics.pstdev(values)
        return {
            "width": image.width,
            "height": image.height,
            "mean_luminance": round(mean, 2),
            "luminance_stddev": round(stddev, 2),
            "nonblank": stddev > 3.0,
        }


def contact_sheet(images: list[Path], output: Path) -> None:
    thumbs: list[tuple[Path, Image.Image]] = []
    for image_path in images:
        image = Image.open(image_path).convert("RGB")
        image.thumbnail((240, 360))
        thumbs.append((image_path, image.copy()))
        image.close()
    columns = 4
    rows = (len(thumbs) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * 260, rows * 395), "#17130f")
    draw = ImageDraw.Draw(sheet)
    for index, (image_path, image) in enumerate(thumbs):
        x = (index % columns) * 260 + 10
        y = (index // columns) * 395 + 10
        sheet.paste(image, (x + (240 - image.width) // 2, y))
        draw.text((x, y + 365), image_path.stem[:36], fill="#f4ead7")
    sheet.save(output)


def main() -> int:
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["NODE_PATH"] = NODE_PATH
    layout = subprocess.run(
        ["node", "scripts/lady_d_finalization/audit_html_layout.mjs"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    try:
        layout_report = json.loads(layout.stdout)
    except json.JSONDecodeError:
        layout_report = {"status": "failed", "stdout": layout.stdout, "stderr": layout.stderr}

    errors: list[str] = []
    if layout.returncode != 0 or layout_report.get("status") != "passed":
        errors.append("HTML layout overflow/browser gate failed")

    rendered: dict[str, object] = {}
    images: list[Path] = []
    for volume, (devotional_name, journal_name) in PDF_NAMES.items():
        records = json.loads(
            (POLISHED_DIR / f"vol{volume}-polished-366-days.json").read_text(encoding="utf-8")
        )
        heaviest = max(
            records,
            key=lambda record: sum(len(paragraph) for paragraph in record["body"]) + len(record["prayer"]),
        )
        heaviest_index = source_index_for_day(heaviest["day"])
        heaviest_page = 2 * heaviest_index + 6
        selections = [
            (PDF_DIR / devotional_name, 1, f"v{volume}-devotional-cover"),
            (PDF_DIR / devotional_name, 9, f"v{volume}-day2-scripture"),
            (PDF_DIR / devotional_name, 10, f"v{volume}-day2-reading"),
            (PDF_DIR / devotional_name, heaviest_page, f"v{volume}-heaviest-day-{heaviest['day']}"),
            (PDF_DIR / journal_name, 1, f"v{volume}-journal-cover"),
            (PDF_DIR / journal_name, 6, f"v{volume}-journal-day2"),
            (PDF_DIR / journal_name, 36, f"v{volume}-january-deep-dive"),
            (PDF_DIR / journal_name, 404, f"v{volume}-december-deep-dive"),
        ]
        for pdf, page_number, label in selections:
            output = RENDER_DIR / f"{label}.png"
            render_page(pdf, page_number, output)
            stats = image_stats(output)
            if not stats["nonblank"]:
                errors.append(f"rendered page appears blank: {label}")
            rendered[label] = {"pdf": pdf.name, "page": page_number, **stats}
            images.append(output)

    sheet_path = RENDER_DIR / "lady-d-six-book-proof-sheet.png"
    contact_sheet(images, sheet_path)
    report = {
        "status": "failed" if errors else "passed",
        "layout": layout_report,
        "rendered_pages": rendered,
        "contact_sheet": str(sheet_path.relative_to(ROOT)),
        "errors": errors,
    }
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
