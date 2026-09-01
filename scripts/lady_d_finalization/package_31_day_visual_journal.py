#!/usr/bin/env python3
"""Build a checksum-manifested delivery package for the concise 31-day journal."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-08-31"
NAME = f"Lady-D-Thirty-One-Mornings-of-Light-Complete-Package-{DATE}.zip"
OUTPUT = ROOT / "output" / NAME
MIRRORS = [
    ROOT / "downloads/lady-d-finalization" / NAME,
    ROOT / "public/downloads/lady-d-finalization" / NAME,
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    files: list[tuple[Path, str]] = [
        (ROOT / "lady-d-31-day-visual-journal.html", "lady-d-31-day-visual-journal.html"),
        (ROOT / "lady-d-31-day-visual-journal-scene-console.html", "lady-d-31-day-visual-journal-scene-console.html"),
        (ROOT / "source/finalization/31-day-visual-journal-v2/visual-journal.json", "source/visual-journal.json"),
        (ROOT / "source/finalization/31-day-visual-journal-v2/visual-journal-plan.json", "source/visual-journal-plan.json"),
        (ROOT / "output/pdf/Lady-D-Thirty-One-Mornings-of-Light-Visual-Journal-6x9.pdf", "print/Lady-D-Thirty-One-Mornings-of-Light-Visual-Journal-6x9.pdf"),
        (ROOT / "quality/31-day-visual-journal-v2/content-and-scene-audit.json", "evidence/content-and-scene-audit.json"),
        (ROOT / "quality/31-day-visual-journal-v2/browser-gauntlet.json", "evidence/browser-gauntlet.json"),
        (ROOT / "quality/31-day-visual-journal-v2/pdf-audit.json", "evidence/pdf-audit.json"),
        (ROOT / "quality/31-day-visual-journal-v2/editorial-judge.json", "evidence/editorial-judge.json"),
    ]
    for scene in sorted((ROOT / "assets/lady-d-31-visual-journal-v2/scenes").glob("day-*.jpg")):
        files.append((scene, f"assets/lady-d-31-visual-journal-v2/scenes/{scene.name}"))
    for font in sorted((ROOT / "assets/fonts").glob("*.ttf")):
        files.append((font, f"assets/fonts/{font.name}"))

    missing = [str(path) for path, _ in files if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing package inputs:\n" + "\n".join(missing))

    entries = [
        {"path": archive_path, "bytes": path.stat().st_size, "sha256": sha256(path)}
        for path, archive_path in files
    ]
    manifest = {
        "schema": "idc.lady_d_31_day_visual_journal_package/v2",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "product": "Thirty-One Mornings of Light - concise visual journal",
        "pageCount": 31,
        "sceneCount": 31,
        "releaseBoundary": "author-review release candidate; final author approval remains required",
        "entries": entries,
    }
    notes = """# Thirty-One Mornings of Light

This is Lady D's concise 31-page visual-journal edition: one unique full-page scene, one short encouragement, one KJV Scripture excerpt, one personal prayer, and one affirmation per day.

The earlier expanded devotional and motion experiences remain demonstrations. This package contains the intended concise print lane, all 31 text-free scene masters, the verified source data, and the production evidence.

Final author approval and a physical print proof remain required before public release.
"""
    checksums = "\n".join(f"{entry['sha256']}  {entry['path']}" for entry in entries) + "\n"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as archive:
        archive.writestr("DELIVERY-NOTES.md", notes)
        archive.writestr("MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
        archive.writestr("SHA256SUMS.txt", checksums)
        for path, archive_path in files:
            archive.write(path, archive_path)
    for mirror in MIRRORS:
        mirror.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(OUTPUT, mirror)
    result = {"status": "PASS", "path": str(OUTPUT), "bytes": OUTPUT.stat().st_size, "sha256": sha256(OUTPUT), "entries": len(entries) + 3, "mirrors": [str(path) for path in MIRRORS]}
    (ROOT / "quality/31-day-visual-journal-v2/package-report.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
