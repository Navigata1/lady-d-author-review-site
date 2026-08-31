#!/usr/bin/env python3
"""Build the complete Lady D client delivery archive."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DATE = "2026-07-19"
PACKAGE_STEM = f"Lady-D-Complete-Publishing-Deliverables-{PACKAGE_DATE}"
ARCHIVE_ROOT = PACKAGE_STEM
OUTPUT = ROOT / "downloads" / "production" / f"{PACKAGE_STEM}.zip"
PUBLIC_OUTPUT = ROOT / "public" / "downloads" / "production" / OUTPUT.name
CHECKSUM_OUTPUT = OUTPUT.with_suffix(".sha256.txt")
PUBLIC_CHECKSUM_OUTPUT = PUBLIC_OUTPUT.with_suffix(".sha256.txt")
ZIP_TIMESTAMP = (2026, 7, 19, 12, 0, 0)


@dataclass(frozen=True)
class DeliveryFile:
    source: Path
    destination: str
    category: str


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def add_file(files: list[DeliveryFile], source: str | Path, destination: str, category: str) -> None:
    path = ROOT / source
    if not path.is_file():
        raise FileNotFoundError(f"Required delivery file is missing: {path}")
    files.append(DeliveryFile(path, destination, category))


def add_directory_files(
    files: list[DeliveryFile],
    source_dir: str,
    destination_dir: str,
    category: str,
    patterns: tuple[str, ...] = ("*",),
    excluded_suffixes: tuple[str, ...] = (),
) -> None:
    base = ROOT / source_dir
    selected: set[Path] = set()
    for pattern in patterns:
        selected.update(path for path in base.glob(pattern) if path.is_file())
    for path in sorted(selected):
        if path.suffix.lower() in excluded_suffixes:
            continue
        relative = path.relative_to(base).as_posix()
        files.append(DeliveryFile(path, f"{destination_dir}/{relative}", category))


def delivery_files() -> list[DeliveryFile]:
    files: list[DeliveryFile] = []

    add_directory_files(
        files,
        "downloads/production/revised-reader-edition/interiors",
        "02-PRINT-INTERIORS",
        "print_interiors",
        patterns=("*.pdf", "*.docx"),
    )

    for volume in (1, 2, 3):
        add_file(
            files,
            f"volume-{volume}-revised-reader-edition.html",
            f"03-READER-HTML/volume-{volume}-revised-reader-edition.html",
            "reader_html",
        )
    add_file(files, "lady-d-revised-trilogy.html", "03-READER-HTML/lady-d-revised-trilogy.html", "reader_html")

    for volume in (1, 2, 3):
        add_directory_files(
            files,
            f"downloads/production/revised-reader-edition/volume-{volume}",
            f"04-EDITABLE-MANUSCRIPTS/volume-{volume}",
            "editable_manuscripts",
            patterns=("*.md", "*.json"),
        )

    quality_files = (
        ("quality/judge/post-rewrite-editorial-judgment.md", "independent-editorial-judgment.md"),
        ("quality/auditor/post-rewrite-manuscript-audit.md", "independent-manuscript-audit.md"),
        ("quality/auditor/post-rewrite-manuscript-audit.json", "independent-manuscript-audit.json"),
        ("quality/visual-proof/post-rewrite-rendered-page-visual-review.md", "rendered-page-visual-review.md"),
        ("downloads/production/revised-reader-edition/lady-d-reader-edition-audit.md", "reader-edition-audit.md"),
        ("downloads/production/revised-reader-edition/lady-d-reader-edition-audit.json", "reader-edition-audit.json"),
        ("downloads/production/revised-reader-edition/interiors/lady-d-revised-interiors-build-audit.json", "interiors-build-audit.json"),
    )
    for source, name in quality_files:
        add_file(files, source, f"05-QUALITY-AND-AUDIT/{name}", "quality_and_audit")

    add_directory_files(
        files,
        "production-assets/author-review-covers",
        "06-COVERS/author-review-covers",
        "cover_assets",
        patterns=("*.png",),
    )
    add_directory_files(
        files,
        "production-assets",
        "06-COVERS/candidate-art",
        "cover_assets",
        patterns=("cover-*-art.png", "volume-*-cover-*-art.png", "three-volume-cover-contact-sheet.png"),
    )
    add_directory_files(
        files,
        "downloads/production/cover-board-docs",
        "06-COVERS/review-board",
        "cover_review",
        patterns=("*.pdf", "*.docx"),
    )
    add_file(
        files,
        "downloads/production/three-volume-cover-candidate-board.md",
        "06-COVERS/review-board/three-volume-cover-candidate-board.md",
        "cover_review",
    )
    for prompt in (
        "Surrendering-to-Gods-Love-10-Cover-Prompts.md",
        "Walking-with-Jesus-10-Cover-Prompts.md",
        "Filled-with-the-Holy-Spirit-10-Cover-Prompts.md",
        "Walking-with-Jesus-31-Day-Visual-Devotional-10-Cover-Prompts.md",
        "Being-Covered-Through-the-Storm-10-Cover-Prompts.md",
    ):
        add_file(files, f"downloads/{prompt}", f"06-COVERS/prompt-packs/{prompt}", "cover_prompts")

    for lane in ("full-wrap-drafts", "companion-journal-full-wrap-drafts"):
        add_directory_files(
            files,
            f"downloads/production/kdp/{lane}",
            f"07-KDP-PREPARATION/{lane}",
            "kdp_wrap_drafts",
            patterns=("*.pdf", "*manifest.md", "*contact-sheet.png"),
        )
    for lane in ("author-decision-sheet", "author-voice-copyedit", "interior-finalization"):
        add_directory_files(
            files,
            f"downloads/production/kdp/{lane}",
            f"07-KDP-PREPARATION/{lane}",
            "kdp_preparation",
            patterns=("*",),
            excluded_suffixes=(".zip",),
        )
    add_directory_files(
        files,
        "downloads/production/kdp",
        "07-KDP-PREPARATION",
        "kdp_preparation",
        patterns=("kdp-trim-cover-readiness-worksheet.*",),
    )

    client_review_files = (
        "susan-damon-hub.html",
        "lady-d-project-dashboard.html",
        "susan-damon-publishing-proposal.html",
        "susan-damon-publishing-proposal.pdf",
        "susan-damon-expanded-invoice.html",
        "susan-damon-expanded-invoice.pdf",
        "lady-d-enhanced-state-of-the-union-2026-07-19.html",
        "lady-d-enhanced-plan-of-attack-2026-07-19.html",
        "STRIPE_1400_PAYMENT_LINK_INSTRUCTIONS.md",
    )
    for source in client_review_files:
        add_file(files, source, f"08-CLIENT-REVIEW/{Path(source).name}", "client_review")

    reproducibility_files = (
        ("scripts/build_lady_d_reader_edition.py", "scripts/build_lady_d_reader_edition.py"),
        ("scripts/build_lady_d_revised_interiors.py", "scripts/build_lady_d_revised_interiors.py"),
        ("scripts/build_lady_d_hub.py", "scripts/build_lady_d_hub.py"),
        ("scripts/build_lady_d_master_delivery.py", "scripts/build_lady_d_master_delivery.py"),
        ("quality/auditor/run_post_rewrite_manuscript_audit.py", "quality/run_post_rewrite_manuscript_audit.py"),
        ("source/research/2026-07-06-transcript-directed-editorial-contract.md", "editorial-contract.md"),
        ("source/scripture/eng-kjv2006_usfm.zip", "scripture/eng-kjv2006_usfm.zip"),
        ("source/scripture/openbible-cross-references.zip", "scripture/openbible-cross-references.zip"),
        ("source/scripture/OPENBIBLE-CROSS-REFERENCES-LICENSE.md", "scripture/OPENBIBLE-CROSS-REFERENCES-LICENSE.md"),
    )
    for source, destination in reproducibility_files:
        add_file(files, source, f"09-REPRODUCIBILITY/{destination}", "reproducibility")

    destinations = [item.destination for item in files]
    if len(destinations) != len(set(destinations)):
        raise ValueError("Duplicate destination detected in master delivery package")
    return sorted(files, key=lambda item: item.destination)


def readme_text(file_count: int) -> str:
    return f"""# Lady D Complete Publishing Deliverables

Prepared: July 19, 2026
Author: Susan \"Lady D\" Damon
Package: {PACKAGE_STEM}

## Start Here

The six primary print files are in `02-PRINT-INTERIORS`:

- Three 6 x 9 devotional reader editions in PDF and DOCX.
- Three 6 x 9 companion journals in PDF and DOCX.

Use `03-READER-HTML` for browser-based review and `04-EDITABLE-MANUSCRIPTS`
for the complete Markdown and JSON manuscript sources. Cover candidates, current
author-review covers, prompt packs, and wrap drafts are grouped under `06-COVERS`
and `07-KDP-PREPARATION`.

## Verified Scope

- 1,098 devotional readings: 366 per volume, including the February 29 bonus.
- 1,098 matched companion-journal units.
- Full KJV Scripture text verified against the archived source.
- Independent editorial judgment: PASS, 95/100.
- Independent full-corpus audit: PASS, 100/100.
- Production-interior artifact gate: PASS.

## Release Boundary

These are review-ready production artifacts. Public Amazon KDP release remains
on hold until Lady D gives final author approval, the files pass KDP Previewer,
and an approved physical proof is documented. Cover images and full wraps in
this package remain review candidates until that approval is recorded.

The corrected package total is $2,000, with $600 paid and $1,400 remaining.
The live $1,400 Stripe Payment Link is still pending account permissions.

## Package Integrity

This archive contains {file_count} delivery files plus this guide, `MANIFEST.json`,
and `SHA256SUMS.txt`. Use the checksum file to verify extracted contents.

Raw meeting audio, private transcripts, caches, and superseded incremental draft
packs are intentionally excluded.
"""


def compression_for(path: str) -> int:
    if Path(path).suffix.lower() in {".zip", ".png", ".pdf", ".docx", ".gif", ".jpg", ".jpeg"}:
        return zipfile.ZIP_STORED
    return zipfile.ZIP_DEFLATED


def write_zip_entry(archive: zipfile.ZipFile, path: str, data: bytes) -> None:
    info = zipfile.ZipInfo(f"{ARCHIVE_ROOT}/{path}", ZIP_TIMESTAMP)
    info.external_attr = 0o100644 << 16
    info.compress_type = compression_for(path)
    archive.writestr(info, data, compress_type=info.compress_type, compresslevel=9)


def build() -> dict[str, object]:
    files = delivery_files()
    payloads: list[tuple[DeliveryFile, bytes]] = [(item, item.source.read_bytes()) for item in files]
    records = [
        {
            "package_path": item.destination,
            "source_path": item.source.relative_to(ROOT).as_posix(),
            "category": item.category,
            "size_bytes": len(data),
            "sha256": sha256_bytes(data),
        }
        for item, data in payloads
    ]
    readme = readme_text(len(records)).encode("utf-8")
    records_with_readme = records + [
        {
            "package_path": "01-START-HERE/README.md",
            "source_path": "generated",
            "category": "start_here",
            "size_bytes": len(readme),
            "sha256": sha256_bytes(readme),
        }
    ]
    manifest = {
        "package": PACKAGE_STEM,
        "prepared_date": PACKAGE_DATE,
        "author": "Susan 'Lady D' Damon",
        "release_status": {
            "manuscript_gate": "PASS",
            "editorial_score": 95,
            "full_corpus_audit": "PASS",
            "audit_score": 100,
            "production_artifact_gate": "PASS",
            "public_kdp_release": "HOLD",
            "remaining_release_gates": [
                "Lady D final author approval",
                "KDP Previewer evidence",
                "approved physical proof",
            ],
        },
        "files": records_with_readme,
    }
    manifest_bytes = (json.dumps(manifest, indent=2, ensure_ascii=True) + "\n").encode("utf-8")
    checksum_rows = [f"{row['sha256']}  {row['package_path']}" for row in records_with_readme]
    checksum_rows.append(f"{sha256_bytes(manifest_bytes)}  01-START-HERE/MANIFEST.json")
    checksums = ("\n".join(checksum_rows) + "\n").encode("utf-8")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", allowZip64=True) as archive:
        write_zip_entry(archive, "01-START-HERE/README.md", readme)
        write_zip_entry(archive, "01-START-HERE/MANIFEST.json", manifest_bytes)
        write_zip_entry(archive, "01-START-HERE/SHA256SUMS.txt", checksums)
        for item, data in payloads:
            write_zip_entry(archive, item.destination, data)

    with zipfile.ZipFile(OUTPUT) as archive:
        bad_file = archive.testzip()
        names = archive.namelist()
        if bad_file:
            raise RuntimeError(f"ZIP integrity failure: {bad_file}")
        forbidden = ("transcript", "2026-07-06-audio", "__pycache__", ".DS_Store")
        exposed = [name for name in names if any(token.lower() in name.lower() for token in forbidden)]
        if exposed:
            raise RuntimeError(f"Private or build-only files entered the archive: {exposed}")

    archive_hash = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    checksum_text = f"{archive_hash}  {OUTPUT.name}\n"
    CHECKSUM_OUTPUT.write_text(checksum_text, encoding="utf-8")
    PUBLIC_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(OUTPUT, PUBLIC_OUTPUT)
    PUBLIC_CHECKSUM_OUTPUT.write_text(checksum_text, encoding="utf-8")

    return {
        "archive": OUTPUT.relative_to(ROOT).as_posix(),
        "public_archive": PUBLIC_OUTPUT.relative_to(ROOT).as_posix(),
        "sha256": archive_hash,
        "size_bytes": OUTPUT.stat().st_size,
        "delivery_files": len(records),
        "zip_entries": len(names),
        "integrity": "PASS",
        "private_source_screen": "PASS",
    }


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
