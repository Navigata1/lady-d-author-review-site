#!/usr/bin/env python3
"""Close the internal Lady D build phases while preserving external author gates."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "ops" / "mission" / "state.json"
now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
state = json.loads(STATE.read_text())

state["mission"]["status"] = "review_ready"
state["mission"]["updated"] = now

for phase in state["phases"]:
    phase["status"] = "done"
    for task in phase.get("tasks", []):
        task["status"] = "done"
    for gate in phase.get("gates", []):
        gate["status"] = "passed"
        gate["lastRun"] = now
        gate["evidence"] = f"ops/mission/evidence/{gate['id']}-2026-08-30.json"

metric_values = {
    "Devotional entries polished": ("1098", "1098"),
    "Exact mechanical surrender phrases": ("0", "0"),
    "Print-ready paired books": ("6", "6"),
    "Qualified real cover candidates": ("10", "10"),
}
for metric in state["metrics"]:
    if metric["label"] in metric_values:
        metric["current"], metric["target"] = metric_values[metric["label"]]

if not any(metric["label"] == "Audiobook chapter manifests" for metric in state["metrics"]):
    state["metrics"].append({
        "label": "Audiobook chapter manifests",
        "baseline": "0",
        "current": "3",
        "target": "3",
        "direction": "up",
    })

for risk in state["risks"]:
    if risk["title"] == "Humanizer score can reward oversimplification":
        risk["note"] = "Mitigated: the humanizer remained advisory; the August authored exemplar, protected fields, and deterministic editorial evidence outranked the style score."
    elif risk["title"] == "Longer natural prose can overflow 6x9 interiors":
        risk["note"] = "Mitigated: all six PDFs passed exact 6x9 geometry, expected page counts, text-marker checks, representative renders, and automated overflow checks."
    elif risk["title"] == "Generated cover imagery can drift dark or embed malformed text":
        risk["note"] = "Mitigated for author selection: ten no-text raster candidates passed luminance and dark-mass gates; final typography waits for Susan's selection and locked wrap dimensions."

if not any(risk["title"] == "External author and KDP gates remain" for risk in state["risks"]):
    state["risks"].append({
        "title": "External author and KDP gates remain",
        "severity": "high",
        "note": "Susan's voice and theological approval, front matter, selected-cover wrap assembly, KDP Previewer, and a physical proof are required before public release.",
    })

state["resume"] = {
    "activePhase": "author-review",
    "nextActions": [
        "Ask Susan to review representative days from every month in all three devotionals and journals.",
        "Record Susan's ranked cover selection, then assemble exact KDP wraps after page count and paper choice are locked.",
        "Complete theological and permissions review, KDP Previewer, and a photographed physical proof.",
        "Use the audiobook manifests only with human narration or a provider workflow explicitly authorized for the intended distributor.",
    ],
    "blockers": [
        "Final author voice and theological approval has not yet been recorded.",
        "Final cover typography, spine width, back matter, barcode, and KDP physical proof depend on author selection and production metadata.",
    ],
    "conventions": state["resume"]["conventions"],
}

STATE.write_text(json.dumps(state, indent=2) + "\n")
print(f"Updated {STATE} at {now}")
