#!/usr/bin/env python3
"""Build checksum-manifested Lady D master and web review packages."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "public"
DOWNLOADS = PUBLIC / "downloads" / "lady-d-finalization"
OUTPUT = ROOT / "output"
DATE = "2026-08-31"
MASTER = OUTPUT / f"Lady-D-Trilogy-Finalization-Master-Package-{DATE}.zip"
WEB = DOWNLOADS / f"Lady-D-Trilogy-Web-Review-Package-{DATE}.zip"
WEB_MIRROR = ROOT / "downloads" / "lady-d-finalization" / WEB.name

PDFS = [
    DOWNLOADS / "Lady-D-Volume-1-Surrendering-to-Gods-Love-Polished-6x9.pdf",
    DOWNLOADS / "Lady-D-Volume-1-Surrendering-to-Gods-Love-Companion-Journal-Deep-Dive-6x9.pdf",
    DOWNLOADS / "Lady-D-Volume-2-Walking-with-Jesus-Polished-6x9.pdf",
    DOWNLOADS / "Lady-D-Volume-2-Walking-with-Jesus-Companion-Journal-Deep-Dive-6x9.pdf",
    DOWNLOADS / "Lady-D-Volume-3-Filled-with-the-Holy-Spirit-Polished-6x9.pdf",
    DOWNLOADS / "Lady-D-Volume-3-Filled-with-the-Holy-Spirit-Companion-Journal-Deep-Dive-6x9.pdf",
]

HTML_INTERIORS = sorted(DOWNLOADS.glob("volume-*-polished-*.html"))
COVERS = sorted((PUBLIC / "covers" / "lady-d-finalization").glob("*.png"))
AUDIOBOOK = sorted((DOWNLOADS / "audiobook").glob("*"))
POLISHED = sorted((ROOT / "source" / "finalization" / "polished").glob("*.json"))

SHARED = [
    ROOT / "susan-damon-hub.html",
    ROOT / "lady-d-finalization-review.html",
    PUBLIC / "lady-d-cover-decision-deck.html",
    DOWNLOADS / "lady-d-cover-qualification.json",
    ROOT / "source" / "finalization" / "cover-prompts.json",
    ROOT / "source" / "finalization" / "evidence" / "lady-d-author-cover-directions.md",
    ROOT / "source" / "finalization" / "evidence" / "lady-d-august-03-voice-exemplar.md",
    ROOT / "source" / "finalization" / "front-matter" / "lady-d-shared-front-matter.json",
    ROOT / "quality" / "finalization" / "voice-polish-report.json",
    ROOT / "ops" / "mission" / "state.json",
    ROOT / "ops" / "mission" / "journal.md",
    ROOT / "ops" / "mission" / "state-of-the-union.html",
] + HTML_INTERIORS + COVERS + AUDIOBOOK

MASTER_FILES = SHARED + PDFS + POLISHED + sorted((ROOT / "ops" / "mission" / "evidence").glob("*.json"))
WEB_FILES = SHARED + POLISHED

NOTES = """# Lady D Trilogy Finalization Delivery

Prepared for Susan \"Lady D\" Damon by IDC Publishing on August 31, 2026.

## Included

- Three polished 366-entry devotionals and three paired deep-dive companion journals.
- Ten real generated cover candidates and the ranked author decision deck.
- Voice-polish evidence, protected-source exemplar, and deterministic audit records.
- Lady D's author-supplied acknowledgments and the tracked status of her requested foreword.
- Three 366-track audiobook manifests and a provider-neutral production blueprint.

## Release boundary

These files are author-review release candidates. Final author voice and theological approval,
the friend's approved foreword, remaining front-matter and Scripture-notice approval, selected-cover wrap typography, KDP Previewer,
and a physical proof remain required before public release.

The internal editorial judge is deterministic automation and is not represented as an
independent human or cross-model review.
"""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def archive_name(path: Path) -> str:
    if path in PDFS or path in HTML_INTERIORS:
        return f"books/{path.name}"
    if path in COVERS:
        return f"covers/{path.name}"
    if path in AUDIOBOOK:
        return f"audiobook/{path.name}"
    if path in POLISHED:
        return f"source/polished/{path.name}"
    if path.parent == ROOT / "ops" / "mission" / "evidence":
        return f"evidence/gates/{path.name}"
    if path.name == "lady-d-finalization-review.html":
        return "review/lady-d-finalization-review.html"
    if path.name == "susan-damon-hub.html":
        return "review/susan-damon-hub.html"
    if path.name == "lady-d-cover-decision-deck.html":
        return "review/lady-d-cover-decision-deck.html"
    if path.name == "lady-d-cover-qualification.json":
        return "evidence/lady-d-cover-qualification.json"
    if path.name == "cover-prompts.json":
        return "evidence/cover-prompts.json"
    if path.name in {"lady-d-author-cover-directions.md", "lady-d-august-03-voice-exemplar.md", "lady-d-shared-front-matter.json"}:
        return f"evidence/{path.name}"
    if path.name == "voice-polish-report.json":
        return "evidence/voice-polish-report.json"
    if path.name in {"state.json", "journal.md", "state-of-the-union.html"}:
        return f"mission/{path.name}"
    raise ValueError(f"No archive mapping for {path}")


def build(destination: Path, files: list[Path], package_kind: str) -> dict:
    destination.parent.mkdir(parents=True, exist_ok=True)
    unique = sorted(set(files), key=lambda item: archive_name(item))
    missing = [str(path) for path in unique if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing package inputs:\n" + "\n".join(missing))

    entries = []
    for path in unique:
        entries.append({
            "path": archive_name(path),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        })

    manifest = {
        "schema": "idc.lady_d_finalization_package/v1",
        "packageKind": package_kind,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "releaseBoundary": "author-review release candidate; not KDP-upload final",
        "entryCount": len(entries),
        "entries": entries,
    }
    checksums = "\n".join(f"{entry['sha256']}  {entry['path']}" for entry in entries) + "\n"

    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as archive:
        archive.writestr("DELIVERY-NOTES.md", NOTES)
        for path in unique:
            archive.write(path, archive_name(path))
        archive.writestr("MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
        archive.writestr("SHA256SUMS.txt", checksums)

    return {
        "path": str(destination),
        "bytes": destination.stat().st_size,
        "sha256": sha256(destination),
        "entries": len(entries) + 3,
    }


def main() -> None:
    master = build(MASTER, MASTER_FILES, "complete-master")
    web = build(WEB, WEB_FILES, "web-review-without-six-large-pdfs")
    WEB_MIRROR.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(WEB, WEB_MIRROR)
    web["root_mirror"] = str(WEB_MIRROR)
    result = {"status": "PASS", "master": master, "web": web}
    (OUTPUT / "lady-d-package-build-report.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
