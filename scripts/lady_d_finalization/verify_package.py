#!/usr/bin/env python3
"""Verify every manifested byte in the Lady D master and web review ZIPs."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-08-31"
PACKAGES = [
    ROOT / "output" / f"Lady-D-Trilogy-Finalization-Master-Package-{DATE}.zip",
    ROOT / "public" / "downloads" / "lady-d-finalization" / f"Lady-D-Trilogy-Web-Review-Package-{DATE}.zip",
    ROOT / "downloads" / "lady-d-finalization" / f"Lady-D-Trilogy-Web-Review-Package-{DATE}.zip",
]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify(path: Path) -> dict:
    errors = []
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        required_meta = {"DELIVERY-NOTES.md", "MANIFEST.json", "SHA256SUMS.txt"}
        if not required_meta.issubset(names):
            errors.append(f"missing metadata: {sorted(required_meta - names)}")
        manifest = json.loads(archive.read("MANIFEST.json"))
        for entry in manifest["entries"]:
            name = entry["path"]
            if name not in names:
                errors.append(f"missing entry: {name}")
                continue
            payload = archive.read(name)
            if len(payload) != entry["bytes"]:
                errors.append(f"size mismatch: {name}")
            if digest(payload) != entry["sha256"]:
                errors.append(f"hash mismatch: {name}")

        checksum_rows = {
            row.split("  ", 1)[1]: row.split("  ", 1)[0]
            for row in archive.read("SHA256SUMS.txt").decode().splitlines()
            if "  " in row
        }
        if len(checksum_rows) != manifest["entryCount"]:
            errors.append("checksum row count differs from manifest")
        if any(checksum_rows.get(item["path"]) != item["sha256"] for item in manifest["entries"]):
            errors.append("checksum file differs from manifest")

    return {
        "path": str(path),
        "status": "PASS" if not errors else "FAIL",
        "manifestEntries": manifest["entryCount"],
        "archiveEntries": len(names),
        "errors": errors,
    }


def main() -> None:
    missing = [str(path) for path in PACKAGES if not path.is_file()]
    if missing:
        raise SystemExit("Missing packages:\n" + "\n".join(missing))
    results = [verify(path) for path in PACKAGES]
    status = "PASS" if all(item["status"] == "PASS" for item in results) else "FAIL"
    report = {"status": status, "packages": results}
    evidence = ROOT / "ops" / "mission" / "evidence" / "P4-G2-2026-08-31.json"
    evidence.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
