#!/usr/bin/env python3
"""Reopen and validate the exported 31-page 6x9 visual-journal PDF."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "output/pdf/Lady-D-Thirty-One-Mornings-of-Light-Visual-Journal-6x9.pdf"
SOURCE = ROOT / "source/finalization/31-day-visual-journal-v2/visual-journal.json"
REPORT = ROOT / "quality/31-day-visual-journal-v2/pdf-audit.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def main() -> None:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    reader = PdfReader(PDF)
    errors: list[str] = []
    records: list[dict[str, object]] = []
    extraction = subprocess.run(
        ["pdftotext", "-layout", str(PDF), "-"],
        capture_output=True,
        text=True,
        check=True,
    )
    extracted_pages = extraction.stdout.split("\f")
    if extracted_pages and not extracted_pages[-1].strip():
        extracted_pages.pop()
    if len(reader.pages) != 31:
        errors.append(f"expected 31 PDF pages, found {len(reader.pages)}")
    for index, page in enumerate(reader.pages, start=1):
        width = round(float(page.mediabox.width), 2)
        height = round(float(page.mediabox.height), 2)
        text = extracted_pages[index - 1] if index <= len(extracted_pages) else ""
        normalized = normalized_text(text)
        expected = source["days"][index - 1] if index <= len(source["days"]) else {}
        if abs(width - 432) > 0.1 or abs(height - 648) > 0.1:
            errors.append(f"page {index} media box is {width}x{height} pt, expected 432x648 pt")
        for required in (f"DAY {index:02d}", expected.get("title", ""), expected.get("reference", ""), "KJV"):
            if required and normalized_text(required) not in normalized:
                errors.append(f"page {index} is missing extracted text {required!r}")
        records.append({"page": index, "widthPoints": width, "heightPoints": height, "textCharacters": len(text)})
    result = {
        "schema": "idc.lady_d_31_day_visual_journal_pdf_audit/v2",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if not errors else "FAIL",
        "path": str(PDF.relative_to(ROOT)),
        "bytes": PDF.stat().st_size,
        "sha256": sha256(PDF),
        "pages": len(reader.pages),
        "trimSize": "6x9 in",
        "mediaBoxPoints": [432, 648],
        "errors": errors,
        "records": records,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("status", "bytes", "sha256", "pages", "trimSize", "mediaBoxPoints", "errors")}, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
