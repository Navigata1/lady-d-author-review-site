#!/usr/bin/env python3
"""Prepare one native image generation as a 300-DPI-ready 6x9 journal scene."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parents[2]
SCENES = ROOT / "assets/lady-d-31-visual-journal-v2/scenes"
MANIFEST = ROOT / "quality/31-day-visual-journal-v2/scene-preparation.json"
TARGET_SIZE = (1800, 2700)


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--day", type=int, required=True)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.day <= 31:
        raise SystemExit("day must be between 1 and 31")
    source = args.input.expanduser().resolve()
    if not source.exists():
        raise SystemExit(f"input image does not exist: {source}")

    with Image.open(source) as opened:
        image = ImageOps.exif_transpose(opened).convert("RGB")
        native_size = image.size
        ratio = image.width / image.height
        if abs(ratio - (2 / 3)) > 0.015:
            raise SystemExit(f"expected a 2:3 image, received {image.width}x{image.height}")
        resized = image.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
        resized = resized.filter(ImageFilter.UnsharpMask(radius=1.2, percent=55, threshold=3))

    SCENES.mkdir(parents=True, exist_ok=True)
    destination = SCENES / f"day-{args.day:02d}.jpg"
    resized.save(destination, "JPEG", quality=95, subsampling=0, optimize=True, dpi=(300, 300))

    manifest = {"schema": "idc.lady_d_scene_preparation/v1", "target": {"width": 1800, "height": 2700, "dpi": 300}, "days": {}}
    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["days"][str(args.day)] = {
        "source": str(source),
        "sourceSha256": digest(source),
        "nativeSize": {"width": native_size[0], "height": native_size[1]},
        "prepared": str(destination.relative_to(ROOT)),
        "preparedSha256": digest(destination),
        "preparedSize": {"width": TARGET_SIZE[0], "height": TARGET_SIZE[1]},
        "status": "prepared-awaiting-visual-gauntlet"
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest["days"][str(args.day)], indent=2))


if __name__ == "__main__":
    main()
