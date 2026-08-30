#!/usr/bin/env python3
"""Audit Lady D final PDFs for size, page count, text markers, and checksums."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PDF_DIR = ROOT / "output/pdf"
EVIDENCE_PATH = ROOT / "ops/mission/evidence/P2-G1-2026-08-30.json"

EXPECTED = {
    "Lady-D-Volume-1-Surrendering-to-Gods-Love-Polished-6x9.pdf": (754, "The Love That Sank Pharaoh's Best"),
    "Lady-D-Volume-1-Surrendering-to-Gods-Love-Companion-Journal-Deep-Dive-6x9.pdf": (420, "Monthly Deep Dive"),
    "Lady-D-Volume-2-Walking-with-Jesus-Polished-6x9.pdf": (754, "The Lord Who Seals a Truth Until Its Hour"),
    "Lady-D-Volume-2-Walking-with-Jesus-Companion-Journal-Deep-Dive-6x9.pdf": (420, "Monthly Deep Dive"),
    "Lady-D-Volume-3-Filled-with-the-Holy-Spirit-Polished-6x9.pdf": (754, "The Prayer That Quenched the Fire"),
    "Lady-D-Volume-3-Filled-with-the-Holy-Spirit-Companion-Journal-Deep-Dive-6x9.pdf": (420, "Monthly Deep Dive"),
}


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def parse_pdfinfo(path: Path) -> dict[str, str]:
    completed = subprocess.run(["pdfinfo", str(path)], check=True, capture_output=True, text=True)
    result: dict[str, str] = {}
    for line in completed.stdout.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip()
    return result


def main() -> int:
    errors: list[str] = []
    files: dict[str, object] = {}
    with tempfile.TemporaryDirectory(prefix="lady-d-pdf-audit-") as temp_dir:
        for filename, (expected_pages, marker) in EXPECTED.items():
            path = PDF_DIR / filename
            if not path.exists():
                errors.append(f"missing PDF: {filename}")
                continue
            info = parse_pdfinfo(path)
            page_count = int(info.get("Pages", "0"))
            page_size = info.get("Page size", "")
            if page_count != expected_pages:
                errors.append(f"{filename}: expected {expected_pages} pages, found {page_count}")
            if not page_size.startswith("432 x 648 pts"):
                errors.append(f"{filename}: expected 6x9 page size, found {page_size}")
            if info.get("Encrypted") != "no":
                errors.append(f"{filename}: PDF unexpectedly encrypted")

            text_path = Path(temp_dir) / f"{path.stem}.txt"
            subprocess.run(["pdftotext", str(path), str(text_path)], check=True)
            text = text_path.read_text(encoding="utf-8", errors="replace")
            if marker not in text:
                errors.append(f"{filename}: missing text marker {marker!r}")
            mechanical = len(re.findall(r"surrender to His love", text, flags=re.IGNORECASE))
            if mechanical:
                errors.append(f"{filename}: mechanical phrase remains {mechanical} time(s)")
            deep_count = text.count("Monthly Deep Dive")
            if "Companion-Journal" in filename and deep_count < 12:
                errors.append(f"{filename}: expected at least 12 monthly deep-dive markers, found {deep_count}")

            files[filename] = {
                "pages": page_count,
                "page_size": page_size,
                "bytes": path.stat().st_size,
                "sha256": digest(path),
                "text_characters": len(text),
                "monthly_deep_dive_markers": deep_count,
            }

    report = {"status": "failed" if errors else "passed", "files": files, "errors": errors}
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
