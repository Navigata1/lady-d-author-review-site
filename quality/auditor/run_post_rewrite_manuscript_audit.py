#!/usr/bin/env python3
"""Independent current-schema audit for the hash-locked Lady D reader edition.

This script is deliberately read-only with respect to manuscripts. It accepts
the one-primary-Scripture schema defined by the binding July 6 contract and
writes only the post-rewrite Markdown and JSON audit reports.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import statistics
import subprocess
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree as ET


REPO = Path(__file__).resolve().parents[2]
CORPUS = REPO / "downloads" / "production" / "revised-reader-edition"
CONTRACT = REPO / "source" / "research" / "2026-07-06-transcript-directed-editorial-contract.md"
KJV_ZIP = REPO / "source" / "scripture" / "eng-kjv2006_usfm.zip"
OPENBIBLE_ZIP = REPO / "source" / "scripture" / "openbible-cross-references.zip"
OPENBIBLE_LICENSE = REPO / "source" / "scripture" / "OPENBIBLE-CROSS-REFERENCES-LICENSE.md"
INTERIORS = CORPUS / "interiors"
INTERIOR_BUILD_AUDIT = INTERIORS / "lady-d-revised-interiors-build-audit.json"
INTERIOR_ZIP = INTERIORS / "Lady-D-Revised-Reader-Edition-Interiors.zip"
VISUAL_REVIEW = REPO / "quality" / "visual-proof" / "post-rewrite-rendered-page-visual-review.md"
JUDGE_REVIEW = REPO / "quality" / "judge" / "post-rewrite-editorial-judgment.md"
OUT_MD = REPO / "quality" / "auditor" / "post-rewrite-manuscript-audit.md"
OUT_JSON = REPO / "quality" / "auditor" / "post-rewrite-manuscript-audit.json"

EXPECTED_JSON_HASHES = {
    1: "531b3f91dd0cb7c361f3277ae250eb11dcc7b9e15fda032e3ad905db8700d290",
    2: "180df45c3be4efb746bf6247f219f02c1acada933df4f9af942b90934a304340",
    3: "bd13507187fca9f42be31b0e7ee271637bf32f8cabdedd7812faadeae18f7675",
}

EXPECTED_KJV_HASH = "4ea6952590d070bfa22985aded48a49581e31b568a60aa09e25f73462e700e7d"
EXPECTED_OPENBIBLE_HASH = "1775644c918fd5751292e3e5bad17461326a1f60537f1838401487a104860b78"
EXPECTED_INTERIOR_ZIP_HASH = "26cb1202ea70d72537e09ded73f270f9f44d3dbae0b6e1fea1be76f6e6a9a22f"
EXPECTED_VISUAL_REVIEW_HASH = "c9cf1ea89480d430bceb09b81dae9dde2898ac930f88a9aa3f3c43a2992e6627"
EXPECTED_JUDGE_REVIEW_HASH = "421e83573b5baf73e480e96cd80919bf9e84c60da7480627d5709d55ad3f828d"

VOLUME_TITLES = {
    1: "Surrendering to God's Love",
    2: "Walking with Jesus",
    3: "Filled with the Holy Spirit",
}

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

BOOK_CODES = {
    "GEN": "Genesis", "EXO": "Exodus", "LEV": "Leviticus", "NUM": "Numbers",
    "DEU": "Deuteronomy", "JOS": "Joshua", "JDG": "Judges", "RUT": "Ruth",
    "1SA": "1 Samuel", "2SA": "2 Samuel", "1KI": "1 Kings", "2KI": "2 Kings",
    "1CH": "1 Chronicles", "2CH": "2 Chronicles", "EZR": "Ezra", "NEH": "Nehemiah",
    "EST": "Esther", "JOB": "Job", "PSA": "Psalm", "PRO": "Proverbs",
    "ECC": "Ecclesiastes", "SNG": "Song of Solomon", "ISA": "Isaiah",
    "JER": "Jeremiah", "LAM": "Lamentations", "EZK": "Ezekiel", "DAN": "Daniel",
    "HOS": "Hosea", "JOL": "Joel", "AMO": "Amos", "OBA": "Obadiah",
    "JON": "Jonah", "MIC": "Micah", "NAM": "Nahum", "HAB": "Habakkuk",
    "ZEP": "Zephaniah", "HAG": "Haggai", "ZEC": "Zechariah", "MAL": "Malachi",
    "MAT": "Matthew", "MRK": "Mark", "LUK": "Luke", "JHN": "John", "ACT": "Acts",
    "ROM": "Romans", "1CO": "1 Corinthians", "2CO": "2 Corinthians",
    "GAL": "Galatians", "EPH": "Ephesians", "PHP": "Philippians",
    "COL": "Colossians", "1TH": "1 Thessalonians", "2TH": "2 Thessalonians",
    "1TI": "1 Timothy", "2TI": "2 Timothy", "TIT": "Titus", "PHM": "Philemon",
    "HEB": "Hebrews", "JAS": "James", "1PE": "1 Peter", "2PE": "2 Peter",
    "1JN": "1 John", "2JN": "2 John", "3JN": "3 John", "JUD": "Jude",
    "REV": "Revelation",
}
BOOK_ORDER = {book: index for index, book in enumerate(BOOK_CODES.values())}

DEPRECATED_LABELS = [
    "Scripture Reference", "Context and language lens", "Today step",
    "Journal prompt", "Morning impact", "Scripture connection",
]

CALENDAR_PATTERN = re.compile(
    r"\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|2026|production calendar)\b",
    re.IGNORECASE,
)
INTERNAL_PATTERN = re.compile(
    r"\b(?:architecture title|production date|production batch|translation review note|"
    r"permissions review|editorial note|final wording and placement|AI model|language model|"
    r"generated prompt|prompt pack|voice filter)\b",
    re.IGNORECASE,
)
READER_META_PATTERN = re.compile(r"\b(?:the reader|this page|this entry|under the title|this lens)\b", re.I)

ROOT_CORE_PATTERN = (
    r"`[^`]+`|\b(?:Hebrew|Greek|Aramaic|ahavah|hesed|shamar|shalom|kyrios|phos|"
    r"sozo|eirene|akoloutheo|pneuma|ruach|parakletos|charis|dunamis|koinonia|"
    r"hagios|emunah|dabaq|yada|gaal|hodos|agape|metanoia|logos|anastasis|"
    r"didaskalos|meno)\b"
)
ROOT_CORE = re.compile(ROOT_CORE_PATTERN, re.IGNORECASE)

TITLE_BAD_PATTERN = re.compile(
    r"\b(?:when let|let see|down talk|in again|the the|and and|to to|in in|for for|"
    r"that become|than become|finds become|at the road|at the waters|in the shore)\b|"
    r"^When (?:Through|in|Teach)\b|^Let (?:Through|in|Teach|Lead|Speak|Form|Rest|Stand|Walk|Carry)\b",
    re.IGNORECASE,
)
TITLE_FUNCTION_WORDS = frozenset({
    "a", "an", "and", "as", "at", "be", "before", "by", "for", "from",
    "he", "her", "him", "his", "i", "in", "into", "is", "it", "its", "me",
    "my", "of", "on", "one", "our", "she", "that", "the", "their", "them",
    "there", "they", "through", "to", "under", "us", "we", "when", "where",
    "with", "you", "your",
})
MISSING_VERB_PATTERN = re.compile(r"\bThis truth in(?: [^,.]+,)* [^.!?]+ by \w+", re.I)
SCRIPTURE_INVITATION_FRAGMENT = re.compile(
    r"^The Scripture's invitation(?:\.|\s+(?:as|before|in|into|over|today|when|where)\b)",
    re.I,
)
SCRIPTURE_INVITATION_FINITE_VERB = re.compile(
    r"\b(?:belongs|begins|means|gives|is|invites|calls|reminds|asks|meets|becomes|"
    r"holds|reveals|brings|comes|points|reaches|starts|makes|teaches|opens|names|"
    r"moves|leads|offers|centers|anchors|rests|forms|draws|turns|requires|carries|takes|shows)\b",
    re.I,
)
MALFORMED_TEACH_ME_REST = re.compile(r"\bteach me rest\b", re.I)
SEVERE_FRAGMENT_PATTERNS = [
    ("malformed Sabbath phrase", re.compile(r"\bas belonging Sabbath rest\b", re.I)),
    ("orphaned neither clause", re.compile(r"^Neither do(?:es)?\b", re.I)),
]

CURRENT_HASH_CONFIRMED_ATTRIBUTION_MISMATCHES: dict[str, dict[str, str]] = {}

CURRENT_HASH_REVIEWED_CONTEXTUAL_NONFAILURES = {
    "V2-D002": {
        "original": "Matthew 16:20", "current": "Mark 8:30",
        "claim": "Mark 8:30 comes after a powerful confession, yet Jesus gives His disciples instruction about what not to announce.",
        "reason": "Archived KJV Mark 8:27 identifies Jesus and His disciples, Mark 8:29 records Peter's confession that Jesus is the Christ, and Mark 8:30 immediately charges them to tell no one. The sentence accurately describes the immediate context and does not misattribute the source verse.",
    },
}

JUDGE_TITLE_REMEDIATIONS = {
    "V1-D001": ("Genesis 15:2", "Questions That Belong Inside the Promise"),
    "V1-D021": ("Exodus 20:6", "Love with a Holy Shape"),
    "V1-D162": ("Genesis 32:32", "Remembering the Mercy That Changed Your Walk"),
    "V1-D289": ("Genesis 1:11", "A Seed Can Carry the Promise"),
    "V1-D315": ("Genesis 50:2", "Love Tends What Remains"),
    "V2-D092": ("Mark 3:18", "Receiving the People Jesus Calls Near"),
    "V2-D214": ("Mark 2:25", "Mercy Is How Jesus Reads the Need"),
    "V2-D247": ("Luke 12:6", "Nothing Small Is Overlooked by the Father"),
    "V2-D350": ("Mark 8:15", "The Hidden Influence Shaping Your Heart"),
    "V2-D364": ("Mark 11:31", "The Honest Answer Obedience Requires"),
    "V2-D365": ("Matthew 20:33", "A Plain Prayer for Open Eyes"),
    "V3-D019": ("Exodus 35:9", "What Is Precious Can Be Prepared for Holy Use"),
    "V3-D152": ("Judges 14:20", "Bringing Relational Grief into God's Presence"),
    "V3-D233": ("Judges 6:5", "Pressure Is Not the Same as God's Absence"),
    "V3-D251": ("Judges 6:29", "Courage While the Questions Are Still Spreading"),
    "V3-D326": ("Numbers 11:28", "When Another Person's Gift Feels Threatening"),
}

JUDGE_DETACHED_PROSE_REMEDIATIONS = {
    "V2-D075": {
        "forbidden": "kingdom life overturns the instinct to protect status",
        "required": "fear loses authority when the heart lets Jesus name His nearness",
    },
    "V3-D152": {
        "forbidden": "spiritual gifts become trustworthy when they serve the body",
        "required": "grief must be brought into God's presence",
    },
    "V3-D233": {
        "forbidden": "Oil for the waiting season closes in this season",
        "required": "overwhelming pressure is not the same as God's absence",
    },
    "V3-D251": {
        "forbidden": "one body and one Spirit",
        "required": "settled courage can tell the truth",
    },
}

JUDGE_GRAMMAR_REMEDIATIONS = {
    "V1-D051": {
        "field": "body", "forbidden": "The Scripture's invitation.",
        "required": "Receive the Scripture's invitation with an honest response.",
    },
    "V1-D096": {
        "field": "body", "forbidden": "The Scripture's invitation over what feels too much to carry.",
        "required": "Let the Scripture's invitation speak over what feels too much to carry.",
    },
    "V1-D109": {
        "field": "body", "forbidden": "The Scripture's invitation.",
        "required": "Before the day turns loud, let the Father define the room.",
    },
    "V1-D158": {
        "field": "body", "forbidden": "The Scripture's invitation.",
        "required": "The Father can turn a road of guilt into a road of witness.",
    },
    "V2-D321": {
        "field": "body", "forbidden": "The Scripture's invitation into the ordinary place where impatience has been growing.",
        "required": "Carry the Scripture's invitation into the ordinary place where impatience has been growing.",
    },
    "V3-D101": {
        "field": "body", "forbidden": "The Scripture's invitation.",
        "required": "Receive the Scripture's invitation with an honest response.",
    },
    "V2-D055": {
        "field": "prayer", "forbidden": "Teach me rest listening",
        "required": "Teach me to rest in listening",
    },
    "V2-D113": {
        "field": "prayer", "forbidden": "Teach me rest stewardship",
        "required": "Teach me to rest in stewardship",
    },
    "V2-D335": {
        "field": "prayer", "forbidden": "teach me rest thanksgiving",
        "required": "teach me to rest in thanksgiving",
    },
    "V3-D057": {
        "field": "prayer", "forbidden": "teach me rest humility",
        "required": "teach me to rest in humility",
    },
}

AUDITOR_NEITHER_REMEDIATIONS = {
    "V2-D041": {
        "reference": "Matthew 13:41",
        "forbidden": "Neither does the sin you are surrendering.",
        "required": "The sin you are surrendering does not have the final word over your life.",
    },
    "V2-D050": {
        "reference": "Matthew 15:11",
        "forbidden": "Neither do your worst words, your reactive moment, or the pressure that exposed you.",
        "required": "Your worst words, your reactive moment, and the pressure that exposed you do not have the final word over the heart Jesus wants to heal.",
    },
    "V2-D052": {
        "reference": "Matthew 17:13",
        "forbidden": "Neither does yesterday's confusion.",
        "required": "Yesterday's confusion does not disqualify today's understanding.",
    },
    "V2-D079": {
        "reference": "Mark 6:3",
        "forbidden": "Neither do other people's small labels.",
        "required": "Other people's small labels do not define what Jesus is forming in you.",
    },
    "V2-D187": {
        "reference": "Mark 8:5",
        "forbidden": "Neither does scarcity, comparison, or the fear that your little is too little.",
        "required": "Scarcity, comparison, and the fear that your little is too little do not limit what Jesus can do with surrendered provision.",
    },
    "V2-D207": {
        "reference": "Mark 8:35",
        "forbidden": "Neither does the sacrifice, the loss, or the obedience you are afraid will cost too much.",
        "required": "The sacrifice, loss, or obedience you fear will cost too much does not outweigh the life Jesus gives.",
    },
    "V2-D212": {
        "reference": "Matthew 15:21",
        "forbidden": "Neither does the region, the transition, the unanswered question, or the place where you feel out of your depth.",
        "required": "The region, the transition, the unanswered question, and the place where you feel out of your depth do not remove you from His leadership.",
    },
    "V2-D325": {
        "reference": "Mark 6:17",
        "forbidden": "Neither does the prison, the accusation, the delay, or the hard backstory.",
        "required": "The prison, the accusation, the delay, and the hard backstory do not place the story beyond Jesus' presence.",
    },
}

REMOVAL_CLAIMS = {
    "living_center": "living center",
    "through_that_line": "Through that line",
    "without_fanfare": "without fanfare",
    "practice_the_scriptures_invitation_by": "Practice the Scripture's invitation by",
}

DEEPENING_OPENERS = (
    "Stay with the verse's own words:",
    "The passage becomes personal in the line,",
    "One phrase deserves an unhurried hearing:",
    "The verse places its truth in front of us:",
    "Listen again to the movement of the text:",
    "The reading turns on these words:",
    "The Scripture brings the moment into focus:",
    "Let this part of the verse come close:",
    "The heart of the passage can be heard here:",
    "Do not hurry past the words,",
    "The verse gives the day a clear center:",
    "Hear the weight carried by this line:",
    "A close reading begins with the words,",
    "The passage asks for attention at this point:",
    "Let the Scripture slow the moment down:",
    "Return once more to the phrase,",
)

LEGACY_THEME_LABELS = (
    "The Surrendered Heart", "Promises That Do Not Fail", "Healing in His Presence",
    "The Cross and Daily Grace", "The Way, the Truth, and the Life",
    "Peace in the Storm", "Rain down on me",
)

STALE_TRANSITION_PATTERN = re.compile(
    r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"(?:'s)?\s+(?:arc|theme)\b|\b(?:arc|theme)\s+(?:for|of)\s+"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\b|"
    r"\b(?:opens?|opened|begins?|began|closes?|closed|ends?|ended)\s+"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\b|"
    r"\b(?:as this year closes|before the year ends|from this year|for the year ahead|"
    r"the fruit of this year|at the end of a year|the end of a year|closes the year|"
    r"ending the year|year-ending|the year can close|close the year|closing the year|"
    r"closes this month|close this month|the first day of this new month|"
    r"first day of this new month|year-end)\b",
    re.I,
)

UNSUPPORTED_READINESS_PATTERN = re.compile(
    r"\b(?:release[- ]ready|publication[- ]ready|KDP[- ]ready|ready for (?:release|publication|KDP)|"
    r"approved for (?:release|publication|KDP)|no further (?:review|proof|editing) (?:is )?required|"
    r"all (?:gates|checks) (?:have )?passed|finalized and ready)\b",
    re.I,
)
UNSUPPORTED_REMOVAL_PATTERN = re.compile(
    r"\b(?:old|legacy|generated|production|template|theme|weekday|calendar|internal)\s+"
    r"(?:copy|language|labels?|phrases?|templates?|claims?|artifacts?|content)\s+"
    r"(?:has been|have been|was|were|is|are)\s+(?:removed|eliminated|cleared)\b|"
    r"\bzero\s+(?:occurrences|instances)\s+of\b",
    re.I,
)
SABBATH_PATTERN = re.compile(r"\bSabbath\b|\bseventh[- ]day\b", re.I)
WEEKDAY_PATTERN = re.compile(
    r"\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b", re.I
)

GOSPEL_MATCH_STOPWORDS = {
    "the", "and", "but", "for", "that", "this", "with", "from", "into", "unto",
    "upon", "then", "than", "there", "their", "them", "they", "shall", "will",
    "would", "should", "could", "have", "hath", "has", "had", "been", "being",
    "were", "was", "are", "is", "not", "his", "him", "her", "she", "our", "you",
    "your", "thee", "thou", "thy", "who", "whom", "whose", "which", "what", "when",
    "where", "therefore", "also", "all", "any", "some", "one", "every", "out", "over",
}

EXCLUDED_BROAD_GOSPEL_SOURCES = {
    "Matthew 12:10", "Matthew 17:20", "Matthew 20:30", "Matthew 21:15", "Matthew 21:28",
}
FORCED_GOSPEL_PARALLEL = ("Matthew 18:3", "Mark 10:15")

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "because", "been", "before", "being",
    "but", "by", "can", "do", "does", "for", "from", "had", "has", "have", "he", "her",
    "him", "his", "i", "if", "in", "into", "is", "it", "its", "let", "may", "me", "my",
    "no", "not", "of", "on", "one", "or", "our", "out", "she", "so", "that", "the", "their",
    "them", "then", "there", "these", "they", "this", "those", "through", "to", "unto", "up",
    "us", "was", "we", "were", "what", "when", "where", "which", "who", "will", "with",
    "would", "ye", "you", "your", "thou", "thy", "thee", "shall", "hath", "doth",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_visual_review_evidence() -> dict[str, Any]:
    text = VISUAL_REVIEW.read_text(encoding="utf-8")
    actual_hash = sha256(VISUAL_REVIEW)
    required_markers = [
        "**Reviewer:** Codex production review",
        "**Disposition:** PASS for representative local rendered-proof inspection",
        "not a claim that every one of the 2,364 PDF pages received individual human inspection",
        "Volume 1 devotional: cover/title page 1, Day 8 on page 12, Day 40 on page 45, Day 112 on page 120, and a Scripture Journey Index page.",
        "Volume 2 devotional: cover/title page 1 and a midyear daily reading on page 180.",
        "Volume 2 journal: a representative daily writing unit on page 180.",
        "Volume 3 devotional: cover/title page 1, a late-year daily reading on page 300, and Scripture Journey Index page 389.",
        "Volume 3 journal: January Review page 36.",
        "A final frozen-build recheck also covered Volume 1 Day 77 on page 84, Volume 2 Day 326 on page 341, Volume 3 Day 184 on page 195, Volume 2 journal page 180, and Volume 3 Scripture Journey Index page 389 after the last title, prose, and journal-prompt corrections.",
        "After the independent judge's title-remediation request, a second frozen-build recheck covered the longest title in each revised volume: Volume 1 Day 64 on page 71, Volume 2 Day 229 on page 241, and Volume 3 Day 295 on page 309.",
        "After the final sentence-level grammar remediation, a third frozen-build recheck covered Volume 1 Day 51 on page 56, Volume 2 Day 55 on page 60, and Volume 3 Day 101 on page 109.",
        "After the final thin-reading threshold correction and ZIP rebuild, a fourth frozen-build recheck covered Volume 2 Day 187 on page 198 from the final proof pack (`26cb1202ea70d72537e09ded73f270f9f44d3dbae0b6e1fea1be76f6e6a9a22f`).",
        "No reviewed page showed blank output, overlapping text, missing glyphs, broken rules, or visibly truncated content.",
        "the Volume 2 journal's diversified prayer-record and follow-through prompts remain usable",
        "The three longest-title pages wrap in a balanced two- or three-line block without clipping, collision, margin intrusion, or displacement of the required devotional sections.",
        "Volume 2 Day 187 now reads as a complete 107-word passage-specific body without the redundant deepening scaffold, and the regenerated page remains balanced and unclipped.",
        "author approval of the final manuscripts and proof PDFs",
        "Amazon KDP Previewer review",
        "review and approval of a physical proof copy",
    ]
    missing_markers = [marker for marker in required_markers if marker not in text]
    frozen_inputs = [
        CORPUS / f"volume-{volume}" / f"volume-{volume}-reader-edition.json"
        for volume in range(1, 4)
    ] + [INTERIOR_ZIP]
    latest_frozen_input_mtime = max(path.stat().st_mtime for path in frozen_inputs)
    visual_review_mtime = VISUAL_REVIEW.stat().st_mtime
    postdates_current_freeze = visual_review_mtime >= latest_frozen_input_mtime
    valid = (
        actual_hash == EXPECTED_VISUAL_REVIEW_HASH
        and not missing_markers
        and postdates_current_freeze
    )
    return {
        "path": str(VISUAL_REVIEW.relative_to(REPO)),
        "expected_sha256": EXPECTED_VISUAL_REVIEW_HASH,
        "verified_sha256": actual_hash,
        "hash_matches": actual_hash == EXPECTED_VISUAL_REVIEW_HASH,
        "missing_scope_or_boundary_markers": missing_markers,
        "postdates_current_frozen_json_and_zip": postdates_current_freeze,
        "visual_review_mtime_epoch": int(visual_review_mtime),
        "latest_frozen_input_mtime_epoch": int(latest_frozen_input_mtime),
        "initial_sampled_pages": 12,
        "frozen_build_recheck_actions": 5,
        "judge_title_recheck_actions": 3,
        "grammar_recheck_actions": 3,
        "thin_threshold_recheck_actions": 1,
        "minimum_distinct_sampled_pages": 22,
        "sampled_reader_volumes": [1, 2, 3],
        "sampled_journal_volumes": [2, 3],
        "volume_1_journal_directly_sampled": False,
        "representative_not_exhaustive": True,
        "valid_for_local_human_rendered_page_flag": valid,
        "valid_for_final_author_approval": False,
        "valid_for_kdp_previewer_gate": False,
        "valid_for_physical_proof_gate": False,
        "classification": (
            "Valid representative local rendered-page visual evidence with explicit release boundaries."
            if valid else "The locked visual review predates the current frozen JSON/interior ZIP or otherwise fails its locked scope; it is not evidence for this final rebuild."
        ),
    }


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_text(value: str) -> str:
    return normalize_space(
        value.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    )


def normalize_key(value: str) -> str:
    value = normalize_text(value).lower()
    value = re.sub(r"[`*_#]", "", value)
    value = re.sub(r"[^a-z0-9']+", " ", value)
    return normalize_space(value)


def words(value: str) -> list[str]:
    return re.findall(r"[A-Za-z][A-Za-z'-]*", value)


def split_sentences(value: str) -> list[str]:
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", normalize_space(value))
        if len(words(sentence)) >= 8
    ]


def split_all_sentences(value: str) -> list[str]:
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", normalize_space(value))
        if sentence.strip()
    ]


def matching_excerpts(value: str, pattern: re.Pattern[str]) -> list[str]:
    candidates = re.split(r"(?<=[.!?])\s+", normalize_space(value))
    return [candidate[:600] for candidate in candidates if pattern.search(candidate)][:5]


def clean_usfm(value: str) -> str:
    value = re.sub(r"\\f\s.*?\\f\*", " ", value, flags=re.S)
    value = re.sub(r"\\x\s.*?\\x\*", " ", value, flags=re.S)
    value = re.sub(r"\\\+?w\s+([^|]+?)\|.*?\\\+?w\*", r"\1", value, flags=re.S)
    value = re.sub(r"\\\+?(?:add|nd|qt|wj|bk|k|pn|sig|sls|tl|it|bd|bdit|em)\s+", "", value)
    value = re.sub(r"\\\+?(?:add|nd|qt|wj|bk|k|pn|sig|sls|tl|it|bd|bdit|em)\*", "", value)
    value = re.sub(r"\\\+?[A-Za-z0-9-]+\*?(?:\s+[^\\\n]*)?", " ", value)
    return normalize_text(value.replace("¶", ""))


def load_kjv() -> tuple[dict[tuple[str, int, int], str], dict[str, Any]]:
    verses: dict[tuple[str, int, int], str] = {}
    file_count = 0
    with zipfile.ZipFile(KJV_ZIP) as archive:
        for name in archive.namelist():
            if not name.endswith(".usfm"):
                continue
            file_count += 1
            match = re.search(r"-([1-3]?[A-Z]{2,3})eng-kjv2006\.usfm$", name)
            if not match or match.group(1) not in BOOK_CODES:
                raise ValueError(f"Unmapped USFM file: {name}")
            book = BOOK_CODES[match.group(1)]
            chapter: int | None = None
            verse: int | None = None
            buffer: list[str] = []

            def flush() -> None:
                nonlocal buffer
                if chapter is not None and verse is not None:
                    verses[(book, chapter, verse)] = clean_usfm(" ".join(buffer))
                buffer = []

            for line in archive.read(name).decode("utf-8-sig").splitlines():
                chapter_match = re.match(r"\\c\s+(\d+)", line)
                if chapter_match:
                    flush()
                    chapter = int(chapter_match.group(1))
                    verse = None
                    continue
                verse_match = re.match(r"\\v\s+(\d+)(?:-\d+)?\s*(.*)", line)
                if verse_match:
                    flush()
                    verse = int(verse_match.group(1))
                    buffer = [verse_match.group(2)]
                elif verse is not None:
                    buffer.append(line)
            flush()
    return verses, {
        "archive_sha256": sha256(KJV_ZIP),
        "usfm_files": file_count,
        "parsed_verses": len(verses),
    }


def parse_reference(reference: str) -> tuple[str, int, int] | None:
    match = re.fullmatch(r"((?:[1-3] )?[A-Za-z]+(?: [A-Za-z]+)*) (\d+):(\d+)", reference.strip())
    if not match:
        return None
    book = "Psalm" if match.group(1) == "Psalms" else match.group(1)
    return book, int(match.group(2)), int(match.group(3))


def expected_dates() -> list[tuple[int, str]]:
    rows: list[tuple[int, str]] = []
    cursor = date(2025, 1, 1)
    for day_number in range(1, 366):
        rows.append((day_number, f"{cursor.strftime('%B')} {cursor.day}"))
        if cursor.month == 2 and cursor.day == 28:
            rows.append((0, "February 29"))
        cursor += timedelta(days=1)
    return rows


def parse_daily_blocks(text: str) -> dict[str, str]:
    pattern = re.compile(r"^## (?P<date>[A-Za-z]+ \d{1,2}) \| (?P<kind>Day \d{3}|Bonus Reading)\s*$", re.M)
    matches = list(pattern.finditer(text))
    blocks: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks[match.group("date")] = text[match.start():end].strip()
    return blocks


def md_contains(block: str, value: str) -> bool:
    return normalize_text(value) in normalize_text(block)


def duplicate_summary(values: Iterable[tuple[str, str]]) -> dict[str, Any]:
    groups: dict[str, list[str]] = defaultdict(list)
    display: dict[str, str] = {}
    for entry_id, value in values:
        key = normalize_key(value)
        if key:
            groups[key].append(entry_id)
            display.setdefault(key, value)
    rows = [
        {"value": display[key], "occurrences": len(ids), "entry_ids": ids}
        for key, ids in groups.items() if len(ids) > 1
    ]
    rows.sort(key=lambda row: (-row["occurrences"], row["value"]))
    return {
        "duplicate_groups": len(rows),
        "affected_entries": len({entry_id for row in rows for entry_id in row["entry_ids"]}),
        "maximum_occurrences": max((row["occurrences"] for row in rows), default=1),
        "groups": rows,
    }


def near_title_pairs(entries: list[dict[str, Any]], threshold: float = 0.90) -> dict[str, Any]:
    rows = []
    for volume in range(1, 4):
        current = [entry for entry in entries if entry["volume"] == volume]
        for index, left in enumerate(current):
            left_key = normalize_key(left["title"])
            for right in current[index + 1:]:
                right_key = normalize_key(right["title"])
                if not left_key or left_key == right_key:
                    continue
                similarity = SequenceMatcher(None, left_key, right_key).ratio()
                if similarity >= threshold:
                    rows.append({
                        "volume": volume, "left": left["id"], "right": right["id"],
                        "left_title": left["title"], "right_title": right["title"],
                        "similarity": round(similarity, 4),
                    })
    rows.sort(key=lambda row: (-row["similarity"], row["left"], row["right"]))
    return {"threshold": threshold, "pair_count": len(rows), "pairs": rows}


def title_factory_audit(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Detect a small repeated suffix bank hidden by exact-title uniqueness."""
    volumes: dict[str, Any] = {}
    for volume in range(1, 4):
        current = [entry for entry in entries if entry["volume"] == volume]
        suffix_counts: Counter[tuple[str, ...]] = Counter()
        suffix_display: dict[tuple[str, ...], str] = {}
        prefix_counts: Counter[tuple[str, ...]] = Counter()
        prefix_display: dict[tuple[str, ...], str] = {}
        for entry in current:
            title_words = words(entry["title"])
            if len(title_words) >= 4:
                prefix = tuple(word.lower() for word in title_words[:4])
                prefix_counts[prefix] += 1
                prefix_display.setdefault(prefix, " ".join(title_words[:4]))
            for length in range(2, min(7, len(title_words)) + 1):
                suffix = tuple(word.lower() for word in title_words[-length:])
                suffix_counts[suffix] += 1
                suffix_display.setdefault(suffix, " ".join(title_words[-length:]))
        repeated = {suffix: count for suffix, count in suffix_counts.items() if count >= 8}
        assignments: dict[str, tuple[str, ...]] = {}
        examples: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
        for entry in current:
            title_words = [word.lower() for word in words(entry["title"])]
            matches = [
                suffix for suffix in repeated
                if len(suffix) <= len(title_words) and tuple(title_words[-len(suffix):]) == suffix
            ]
            if not matches:
                continue
            longest = max(matches, key=len)
            assignments[entry["id"]] = longest
            if len(examples[longest]) < 4:
                examples[longest].append({"entry_id": entry["id"], "title": entry["title"]})
        assigned_counts = Counter(assignments.values())
        groups = [
            {
                "suffix": suffix_display[suffix],
                "words": len(suffix),
                "occurrences": count,
                "examples": examples[suffix],
            }
            for suffix, count in assigned_counts.most_common()
        ]
        affected = len(assignments)
        affected_share = affected / max(1, len(current))
        suffix_factory_pattern = affected_share >= 0.75 and len(assigned_counts) <= 40
        repeated_prefixes = {prefix: count for prefix, count in prefix_counts.items() if count >= 10}
        prefix_affected = sum(repeated_prefixes.values())
        prefix_affected_share = prefix_affected / max(1, len(current))
        prefix_factory_pattern = prefix_affected_share >= 0.50
        prefix_groups = [
            {
                "prefix": prefix_display[prefix],
                "words": 4,
                "occurrences": count,
                "examples": [
                    {"entry_id": entry["id"], "title": entry["title"]}
                    for entry in current
                    if tuple(word.lower() for word in words(entry["title"])[:4]) == prefix
                ][:4],
            }
            for prefix, count in sorted(
                repeated_prefixes.items(), key=lambda item: (-item[1], item[0])
            )
        ]
        factory_pattern = suffix_factory_pattern or prefix_factory_pattern
        volumes[str(volume)] = {
            "entries": len(current),
            "colon_titles": sum(":" in entry["title"] for entry in current),
            "repeated_suffix_minimum_occurrences": 8,
            "factory_affected_entries": affected,
            "factory_affected_share": round(affected_share, 4),
            "distinct_assigned_suffix_groups": len(assigned_counts),
            "suffix_factory_pattern_detected": suffix_factory_pattern,
            "repeated_prefix_minimum_occurrences": 10,
            "prefix_factory_affected_entries": prefix_affected,
            "prefix_factory_affected_share": round(prefix_affected_share, 4),
            "distinct_repeated_prefix_groups": len(repeated_prefixes),
            "prefix_factory_pattern_detected": prefix_factory_pattern,
            "factory_pattern_detected": factory_pattern,
            "top_suffix_groups": groups[:40],
            "top_prefix_groups": prefix_groups[:40],
            "unassigned_entry_ids": sorted({entry["id"] for entry in current} - set(assignments)),
        }
    return {
        "method": "Two independent factory screens are applied per volume: (1) assign each title its longest final 2-7 word suffix occurring at least eight times and flag when at least 75% of titles map to no more than 40 such endings; (2) reproduce the judge's sentence-derived-title concern by grouping exact four-word prefixes used at least ten times and flag when those families affect at least 50% of a volume.",
        "volumes": volumes,
        "volumes_with_factory_pattern": [
            int(volume) for volume, result in volumes.items() if result["factory_pattern_detected"]
        ],
        "total_colon_titles": sum(result["colon_titles"] for result in volumes.values()),
    }


def title_naturalness(entry: dict[str, Any]) -> list[str]:
    title = entry["title"]
    reasons = []
    if TITLE_BAD_PATTERN.search(title):
        reasons.append("malformed connector/preposition pattern")
    parts = [normalize_key(part) for part in title.split(":") if normalize_key(part)]
    if len(parts) > 1 and any(
        left == right or left in right or right in left
        for index, left in enumerate(parts)
        for right in parts[index + 1:]
    ):
        reasons.append("duplicated title clause")
    if title[:1].islower():
        reasons.append("lowercase title start")
    return reasons


def repeated_meaningful_title_words(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for entry in entries:
        tokens = [word.lower() for word in words(entry["title"])]
        counts = Counter(word for word in tokens if word not in TITLE_FUNCTION_WORDS)
        repeated = sorted(word for word, count in counts.items() if count > 1)
        if repeated:
            rows.append({
                "entry_id": entry["id"], "title": entry["title"],
                "repeated_meaningful_words": repeated,
            })
    return rows


def judge_remediation_audit(entries: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {entry["id"]: entry for entry in entries}
    judge_text = JUDGE_REVIEW.read_text(encoding="utf-8")
    judge_hash = sha256(JUDGE_REVIEW)
    failures = []
    title_rows = []
    source_list_missing_ids = []
    for entry_id, (expected_reference, expected_title) in JUDGE_TITLE_REMEDIATIONS.items():
        entry = by_id.get(entry_id)
        if entry is None:
            failures.append(f"{entry_id}: missing from frozen corpus")
            continue
        reasons = title_naturalness(entry)
        matches = (
            entry["scripture_reference"] == expected_reference
            and entry["title"] == expected_title
            and not reasons
        )
        title_rows.append({
            "entry_id": entry_id,
            "scripture_reference": entry["scripture_reference"],
            "expected_reference": expected_reference,
            "title": entry["title"],
            "expected_remediated_title": expected_title,
            "naturalness_flags": reasons,
            "pass": matches,
        })
        if not matches:
            failures.append(f"{entry_id}: judge-listed title remediation does not match reviewed current evidence")

    detached_rows = []
    for entry_id, expectation in JUDGE_DETACHED_PROSE_REMEDIATIONS.items():
        if entry_id not in judge_text:
            source_list_missing_ids.append(entry_id)
        entry = by_id.get(entry_id)
        if entry is None:
            failures.append(f"{entry_id}: missing from frozen corpus")
            continue
        reader_text = normalize_text(" ".join(reader_facing_values(entry).values()))
        body_text = normalize_text(" ".join(entry["body"]))
        forbidden_absent = expectation["forbidden"].lower() not in reader_text.lower()
        replacement_present = expectation["required"].lower() in body_text.lower()
        detached_rows.append({
            "entry_id": entry_id,
            "forbidden_phrase": expectation["forbidden"],
            "forbidden_phrase_absent": forbidden_absent,
            "required_passage_specific_replacement": expectation["required"],
            "replacement_present": replacement_present,
            "pass": forbidden_absent and replacement_present,
        })
        if not forbidden_absent or not replacement_present:
            failures.append(f"{entry_id}: detached-prose remediation failed")

    grammar_rows = []
    for entry_id, expectation in JUDGE_GRAMMAR_REMEDIATIONS.items():
        if entry_id not in judge_text:
            source_list_missing_ids.append(entry_id)
        entry = by_id.get(entry_id)
        if entry is None:
            failures.append(f"{entry_id}: missing from frozen corpus")
            continue
        field = expectation["field"]
        value = normalize_text(
            " ".join(entry[field]) if isinstance(entry[field], list) else entry[field]
        )
        if field == "body":
            forbidden_absent = normalize_text(expectation["forbidden"]).lower() not in {
                normalize_text(sentence).lower() for sentence in split_all_sentences(value)
            }
        else:
            forbidden_absent = expectation["forbidden"].lower() not in value.lower()
        replacement_present = expectation["required"].lower() in value.lower()
        grammar_rows.append({
            "entry_id": entry_id,
            "field": field,
            "forbidden_text": expectation["forbidden"],
            "forbidden_text_absent": forbidden_absent,
            "required_replacement": expectation["required"],
            "replacement_present": replacement_present,
            "pass": forbidden_absent and replacement_present,
        })
        if not forbidden_absent or not replacement_present:
            failures.append(f"{entry_id}: judge-listed grammar remediation failed")

    if judge_hash != EXPECTED_JUDGE_REVIEW_HASH:
        failures.append("Judge remediation source hash does not match the locked checklist")
    return {
        "source_path": str(JUDGE_REVIEW.relative_to(REPO)),
        "expected_source_sha256": EXPECTED_JUDGE_REVIEW_HASH,
        "verified_source_sha256": judge_hash,
        "source_list_missing_ids": sorted(set(source_list_missing_ids)),
        "reviewed_title_rows": title_rows,
        "reviewed_title_count": len(title_rows),
        "detached_prose_rows": detached_rows,
        "detached_prose_count": len(detached_rows),
        "grammar_remediation_rows": grammar_rows,
        "grammar_remediation_count": len(grammar_rows),
        "failures": failures,
        "pass": not failures,
        "scope_note": "The independent judge report is hash-locked only as a checklist; shorthand identifiers in its prose are nonbinding. Current titles, references, reader text, replacement prose, and all ten named grammar repairs are verified directly against the new JSON hash lock.",
    }


def auditor_neither_remediation_audit(entries: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {entry["id"]: entry for entry in entries}
    rows = []
    failures = []
    for entry_id, expectation in AUDITOR_NEITHER_REMEDIATIONS.items():
        entry = by_id.get(entry_id)
        if entry is None:
            failures.append(f"{entry_id}: missing from frozen corpus")
            continue
        body_text = normalize_text(" ".join(entry["body"]))
        body_sentences = {
            normalize_text(sentence).lower()
            for paragraph in entry["body"]
            for sentence in split_all_sentences(paragraph)
        }
        reference_matches = entry["scripture_reference"] == expectation["reference"]
        forbidden_absent = normalize_text(expectation["forbidden"]).lower() not in body_sentences
        replacement_present = normalize_text(expectation["required"]).lower() in body_text.lower()
        passed = reference_matches and forbidden_absent and replacement_present
        rows.append({
            "entry_id": entry_id,
            "scripture_reference": entry["scripture_reference"],
            "expected_reference": expectation["reference"],
            "forbidden_sentence": expectation["forbidden"],
            "forbidden_sentence_absent": forbidden_absent,
            "required_replacement": expectation["required"],
            "replacement_present": replacement_present,
            "pass": passed,
        })
        if not passed:
            failures.append(f"{entry_id}: auditor-led neither-clause remediation failed")

    scripture_literal_rows = []
    for entry in entries:
        if re.search(r"\bNeither do(?:es)?\b", entry["scripture_text"], re.I):
            scripture_literal_rows.append({
                "entry_id": entry["id"],
                "scripture_reference": entry["scripture_reference"],
                "text": entry["scripture_text"],
                "classification": "exact KJV scripture_text; excluded from reader-prose grammar rule",
            })
    mark_11_33_literal_verified = any(
        row["scripture_reference"] == "Mark 11:33"
        and "Neither do I tell you by what authority I do these things." in row["text"]
        for row in scripture_literal_rows
    )
    if not mark_11_33_literal_verified:
        failures.append("Mark 11:33 KJV neither-clause exception was not verified in scripture_text")

    return {
        "configured_rows": len(AUDITOR_NEITHER_REMEDIATIONS),
        "remediation_rows": rows,
        "scripture_text_literals_excluded": scripture_literal_rows,
        "mark_11_33_literal_verified": mark_11_33_literal_verified,
        "rule_scope": "Sentence-leading Neither do/Neither does is prohibited in reader prose fields; exact KJV scripture_text is concordance-checked separately and excluded from this grammar rule.",
        "failures": failures,
        "pass": not failures,
    }


def sequence_metrics(entries: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [entry for entry in entries if entry["day_number"] != 0]
    refs = [parse_reference(entry["scripture_reference"]) for entry in rows]
    adjacent_book = adjacent_chapter = monotonic = 0
    runs: list[tuple[int, int]] = []
    start = 0
    for index in range(1, len(rows)):
        left, right = refs[index - 1], refs[index]
        if left and right and left[0] == right[0]:
            adjacent_book += 1
            if left[1] == right[1]:
                adjacent_chapter += 1
            if (right[1], right[2]) >= (left[1], left[2]):
                monotonic += 1
        else:
            runs.append((start, index - 1))
            start = index
    runs.append((start, len(rows) - 1))
    run_rows = [{
        "book": refs[left][0] if refs[left] else "INVALID",
        "start": rows[left]["date"], "end": rows[right]["date"], "length": right - left + 1,
    } for left, right in runs]
    run_rows.sort(key=lambda row: (-row["length"], row["start"]))
    monthly = []
    for month in MONTHS:
        month_rows = [entry for entry in rows if entry["date"].startswith(month)]
        counts = Counter((parse_reference(entry["scripture_reference"]) or ("INVALID",))[0] for entry in month_rows)
        book, count = counts.most_common(1)[0]
        monthly.append({
            "month": month, "entries": len(month_rows), "distinct_books": len(counts),
            "dominant_book": book, "dominant_count": count,
            "dominant_share": round(count / len(month_rows), 4),
        })
    return {
        "dated_entries": len(rows), "distinct_books": len({ref[0] for ref in refs if ref}),
        "adjacent_same_book_transitions": adjacent_book,
        "adjacent_same_book_rate": round(adjacent_book / max(1, len(rows) - 1), 4),
        "adjacent_same_chapter_transitions": adjacent_chapter,
        "monotonic_same_book_transitions": monotonic,
        "longest_same_book_run": run_rows[0],
        "runs_over_7": [row for row in run_rows if row["length"] > 7],
        "monthly": monthly,
        "months_over_40_percent_one_book": [row for row in monthly if row["dominant_share"] > 0.40],
        "months_under_4_books": [row for row in monthly if row["distinct_books"] < 4],
        "months_over_85_percent_one_book": [row for row in monthly if row["dominant_share"] > 0.85],
        "months_under_2_books": [row for row in monthly if row["distinct_books"] < 2],
    }


def repetition_audit(entries: list[dict[str, Any]]) -> dict[str, Any]:
    exact: dict[str, list[dict[str, str]]] = defaultdict(list)
    templates: dict[str, list[dict[str, str]]] = defaultdict(list)
    within = []
    grams: dict[str, set[str]] = defaultdict(set)
    for entry in entries:
        fields = {
            "context": entry["context"], "body": " ".join(entry["body"]),
            "closing": entry["closing"], "prayer": entry["prayer"],
            "response": entry["reflection_and_response"],
        }
        local = Counter()
        for field, value in fields.items():
            for sentence in split_sentences(value):
                key = normalize_key(sentence)
                exact[key].append({"entry_id": entry["id"], "field": field, "sentence": sentence})
                local[(field, key)] += 1
                masked = sentence
                for replacement in (
                    entry["scripture_reference"], entry["title"],
                    entry.get("theme_name", ""), entry.get("theme_promise", ""),
                ):
                    if replacement:
                        masked = re.sub(re.escape(replacement), "<VARIABLE>", masked, flags=re.I)
                masked = re.sub(r"(?:[1-3] )?[A-Za-z]+(?: [A-Za-z]+)* \d+:\d+", "<REF>", masked)
                masked_key = normalize_key(masked)
                if masked_key not in {"", "variable", "ref"}:
                    templates[masked_key].append({"entry_id": entry["id"], "field": field, "sentence": sentence})
            tokens = normalize_key(value).split()
            for index in range(max(0, len(tokens) - 7)):
                grams[" ".join(tokens[index:index + 8])].add(entry["id"])
        for (field, sentence), count in local.items():
            if count > 1:
                within.append({"entry_id": entry["id"], "field": field, "occurrences": count, "sentence": sentence})

    exact_groups = []
    for _, rows in exact.items():
        ids = sorted({row["entry_id"] for row in rows})
        if len(ids) > 1:
            exact_groups.append({"sentence": rows[0]["sentence"], "occurrences": len(ids), "entry_ids": ids})
    exact_groups.sort(key=lambda row: (-row["occurrences"], row["sentence"]))
    template_groups = []
    for key, rows in templates.items():
        ids = sorted({row["entry_id"] for row in rows})
        originals = {normalize_key(row["sentence"]) for row in rows}
        if len(ids) > 3 and len(originals) > 1:
            template_groups.append({
                "template": key, "occurrences": len(ids), "entry_ids": ids,
                "examples": [row["sentence"] for row in rows[:3]],
            })
    template_groups.sort(key=lambda row: (-row["occurrences"], row["template"]))
    gram_groups = [
        {"phrase": phrase, "affected_entries": len(ids), "entry_ids": sorted(ids)}
        for phrase, ids in grams.items() if len(ids) > 3
    ]
    gram_groups.sort(key=lambda row: (-row["affected_entries"], row["phrase"]))
    return {
        "exact_repeated_sentence_groups": len(exact_groups),
        "exact_repetition_affected_entries": len({entry_id for row in exact_groups for entry_id in row["entry_ids"]}),
        "maximum_exact_sentence_reuse": max((row["occurrences"] for row in exact_groups), default=1),
        "within_entry_duplicate_sentences": len(within),
        "within_entry_examples": within,
        "masked_template_groups_over_3": len(template_groups),
        "template_affected_entries": len({entry_id for row in template_groups for entry_id in row["entry_ids"]}),
        "shared_eight_word_grams_over_3": len(gram_groups),
        "all_exact_groups": exact_groups,
        "all_template_groups": template_groups,
        "top_shared_eight_word_grams": gram_groups[:60],
    }


def removal_claim_audit(entries: list[dict[str, Any]]) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for key, phrase in REMOVAL_CLAIMS.items():
        matches = []
        for entry in entries:
            fields = {
                "title": entry["title"], "context": entry["context"],
                "body": " ".join(entry["body"]), "closing": entry["closing"],
                "prayer": entry["prayer"], "response": entry["reflection_and_response"],
                "journal_observe": entry["journal_observe"],
                "journal_reflect": entry["journal_reflect"], "journal_act": entry["journal_act"],
                "journal_prayer_record": entry["journal_prayer_record"],
                "journal_follow_through": entry["journal_follow_through"],
            }
            for field, value in fields.items():
                if phrase.lower() in value.lower():
                    matches.append({
                        "entry_id": entry["id"], "volume": entry["volume"], "field": field,
                        "phrase": phrase, "excerpts": matching_excerpts(value, re.compile(re.escape(phrase), re.I)),
                    })
        results[key] = {
            "phrase": phrase, "occurrences": len(matches),
            "affected_entries": len({row["entry_id"] for row in matches}),
            "by_volume": dict(Counter(str(row["volume"]) for row in matches)),
            "matches": matches,
        }
    return {
        "claims": results,
        "all_claimed_phrases_absent": all(result["occurrences"] == 0 for result in results.values()),
    }


def deepening_scaffold_audit(entries: list[dict[str, Any]]) -> dict[str, Any]:
    detected = []
    threshold_violations = []
    remaining_thin_without_scaffold = []
    by_volume: dict[str, Any] = {}
    for entry in entries:
        body = entry.get("body") or []
        final_paragraph = body[-1] if body else ""
        opener = next((value for value in DEEPENING_OPENERS if final_paragraph.startswith(value)), "")
        if not opener:
            if entry["volume"] in {2, 3} and len(" ".join(body).split()) < 100:
                remaining_thin_without_scaffold.append({
                    "entry_id": entry["id"], "volume": entry["volume"],
                    "body_words": len(" ".join(body).split()),
                })
            continue
        pre_scaffold_words = len(" ".join(body[:-1]).split())
        row = {
            "entry_id": entry["id"], "volume": entry["volume"], "opener": opener,
            "pre_scaffold_words": pre_scaffold_words,
            "final_body_words": len(" ".join(body).split()),
        }
        detected.append(row)
        if pre_scaffold_words >= 100:
            threshold_violations.append({
                **row, "reason": "Deepening scaffold was added to a body already at or above 100 words.",
            })
    for volume in range(1, 4):
        rows = [row for row in detected if row["volume"] == volume]
        by_volume[str(volume)] = {
            "actual": len(rows),
            "pre_scaffold_words_minimum": min((row["pre_scaffold_words"] for row in rows), default=None),
            "pre_scaffold_words_maximum": max((row["pre_scaffold_words"] for row in rows), default=None),
            "opener_distribution": dict(Counter(row["opener"] for row in rows)),
        }
    d187 = next((entry for entry in entries if entry["id"] == "V2-D187"), None)
    d187_body = d187.get("body", []) if d187 else []
    d187_final_paragraph = d187_body[-1] if d187_body else ""
    d187_opener = next(
        (value for value in DEEPENING_OPENERS if d187_final_paragraph.startswith(value)),
        "",
    )
    d187_final_check = {
        "entry_id": "V2-D187",
        "scripture_reference": d187.get("scripture_reference") if d187 else None,
        "paragraphs": len(d187_body),
        "whitespace_word_count": len(" ".join(d187_body).split()),
        "controlled_deepening_opener": d187_opener or None,
        "expected_paragraphs": 4,
        "expected_whitespace_word_count": 107,
        "pass": bool(
            d187
            and d187.get("scripture_reference") == "Mark 8:5"
            and len(d187_body) == 4
            and len(" ".join(d187_body).split()) == 107
            and not d187_opener
        ),
    }
    return {
        "detection_method": "A deepening paragraph is the final body paragraph and begins with one of the 16 controlled close-reading openers. Pre-scaffold word count is recomputed from all preceding body paragraphs using whitespace tokenization, matching the under-100 threshold.",
        "actual_total": len(detected),
        "by_volume": by_volume,
        "threshold_violations": threshold_violations,
        "remaining_thin_without_scaffold": remaining_thin_without_scaffold,
        "detected_entries": detected,
        "v2_d187_final_remediation": d187_final_check,
        "pass": not threshold_violations and d187_final_check["pass"],
    }


def reader_facing_values(entry: dict[str, Any]) -> dict[str, str]:
    return {
        "title": entry["title"], "context": entry["context"],
        "body": " ".join(entry["body"]), "closing": entry["closing"],
        "prayer": entry["prayer"], "response": entry["reflection_and_response"],
        "journal_observe": entry["journal_observe"],
        "journal_reflect": entry["journal_reflect"], "journal_act": entry["journal_act"],
        "journal_prayer_record": entry["journal_prayer_record"],
        "journal_follow_through": entry["journal_follow_through"],
    }


def reader_facing_hygiene_audit(entries: list[dict[str, Any]]) -> dict[str, Any]:
    old_theme_hits = []
    stale_transition_hits = []
    weekday_hits = []
    unsupported_readiness_claims = []
    unsupported_removal_claims = []
    sabbath_rows = []
    detached_sabbath_failures = []
    for entry in entries:
        values = reader_facing_values(entry)
        sabbath_fields = []
        for field, value in values.items():
            for label in LEGACY_THEME_LABELS:
                if re.search(rf"\b{re.escape(label)}\b", value, re.I):
                    old_theme_hits.append({
                        "entry_id": entry["id"], "field": field, "label": label,
                        "excerpts": matching_excerpts(value, re.compile(re.escape(label), re.I)),
                    })
            if STALE_TRANSITION_PATTERN.search(value):
                stale_transition_hits.append({
                    "entry_id": entry["id"], "field": field,
                    "excerpts": matching_excerpts(value, STALE_TRANSITION_PATTERN),
                })
            if WEEKDAY_PATTERN.search(value):
                weekday_hits.append({
                    "entry_id": entry["id"], "field": field,
                    "matches": WEEKDAY_PATTERN.findall(value),
                    "excerpts": matching_excerpts(value, WEEKDAY_PATTERN),
                })
            if UNSUPPORTED_READINESS_PATTERN.search(value):
                unsupported_readiness_claims.append({
                    "entry_id": entry["id"], "field": field,
                    "excerpts": matching_excerpts(value, UNSUPPORTED_READINESS_PATTERN),
                })
            if UNSUPPORTED_REMOVAL_PATTERN.search(value):
                unsupported_removal_claims.append({
                    "entry_id": entry["id"], "field": field,
                    "excerpts": matching_excerpts(value, UNSUPPORTED_REMOVAL_PATTERN),
                })
            if SABBATH_PATTERN.search(value):
                sabbath_fields.append(field)
        if sabbath_fields:
            theme_justified = entry.get("theme_name") == "Rest in the Father's Care"
            scripture_justified = bool(SABBATH_PATTERN.search(entry["scripture_text"]))
            row = {
                "entry_id": entry["id"], "volume": entry["volume"], "date": entry["date"],
                "reference": entry["scripture_reference"], "theme": entry.get("theme_name", ""),
                "reader_fields": sabbath_fields,
                "theme_justified": theme_justified,
                "direct_scripture_justified": scripture_justified,
                "justification": (
                    "Rest in the Father's Care theme" if theme_justified
                    else "primary Scripture explicitly names Sabbath/seventh day" if scripture_justified
                    else "none"
                ),
            }
            sabbath_rows.append(row)
            if not theme_justified and not scripture_justified:
                detached_sabbath_failures.append(row)
    return {
        "reader_fields_checked": list(reader_facing_values(entries[0]).keys()) if entries else [],
        "legacy_theme_labels_checked": list(LEGACY_THEME_LABELS),
        "old_theme_label_hits": old_theme_hits,
        "stale_month_year_transition_hits": stale_transition_hits,
        "weekday_hits": weekday_hits,
        "unsupported_readiness_claims": unsupported_readiness_claims,
        "unsupported_removal_claims": unsupported_removal_claims,
        "explicit_sabbath_entries": sabbath_rows,
        "explicit_sabbath_entries_by_volume": dict(Counter(str(row["volume"]) for row in sabbath_rows)),
        "sabbath_justification_counts": dict(Counter(row["justification"] for row in sabbath_rows)),
        "detached_sabbath_failures": detached_sabbath_failures,
        "pass": not any([
            old_theme_hits, stale_transition_hits, weekday_hits,
            unsupported_readiness_claims, unsupported_removal_claims,
            detached_sabbath_failures,
        ]),
    }


def severe_generated_template_audit(entries: list[dict[str, Any]]) -> dict[str, Any]:
    frames: dict[str, list[dict[str, str]]] = defaultdict(list)
    approved_frames = {"then sit with this question"}
    for entry in entries:
        fields = reader_facing_values(entry)
        for field in ("context", "body", "closing", "prayer", "response", "journal_reflect", "journal_act"):
            for sentence in split_sentences(fields[field]):
                if ":" not in sentence:
                    continue
                prefix = sentence.split(":", 1)[0]
                key = normalize_key(prefix)
                if key in approved_frames or not 4 <= len(words(prefix)) <= 16:
                    continue
                frames[key].append({
                    "entry_id": entry["id"], "field": field, "frame": prefix,
                    "sentence": sentence[:360],
                })
    groups = []
    for rows in frames.values():
        entry_ids = sorted({row["entry_id"] for row in rows})
        if len(entry_ids) > 3:
            groups.append({
                "frame": rows[0]["frame"], "affected_entries": len(entry_ids),
                "entry_ids": entry_ids, "examples": rows[:4],
            })
    groups.sort(key=lambda row: (-row["affected_entries"], row["frame"]))
    severe = [row for row in groups if row["affected_entries"] > 30]
    return {
        "method": "Repeated colon-led sentence frames are reported above three entries and fail as severe above thirty entries. The contract-required 'Then sit with this question' journal frame is explicitly excluded.",
        "severe_threshold": 30,
        "repeated_frame_groups_over_3": groups,
        "severe_frame_groups": severe,
        "maximum_frame_reuse": max((row["affected_entries"] for row in groups), default=0),
        "pass": not severe,
    }


def journal_repetition(entries: list[dict[str, Any]]) -> dict[str, Any]:
    fields = [
        "journal_observe", "journal_reflect", "journal_act",
        "journal_prayer_record", "journal_follow_through",
    ]
    by_field = {}
    for field in fields:
        by_field[field] = duplicate_summary((entry["id"], entry[field]) for entry in entries)
    substantive = ["journal_reflect", "journal_act"]
    severe_substantive = {
        field: [row for row in by_field[field]["groups"] if row["occurrences"] > 3]
        for field in substantive
    }
    scaffold = ["journal_observe", "journal_prayer_record", "journal_follow_through"]
    severe_scaffold = {
        field: [row for row in by_field[field]["groups"] if row["occurrences"] > 30]
        for field in scaffold
    }
    return {
        "by_field": by_field,
        "substantive_groups_over_3": severe_substantive,
        "substantive_severe_group_count": sum(len(rows) for rows in severe_substantive.values()),
        "scaffold_groups_over_30": severe_scaffold,
        "scaffold_severe_group_count": sum(len(rows) for rows in severe_scaffold.values()),
        "note": "Observe/prayer-record/follow-through are reported separately as journal scaffolding; reflect and act are treated as day-specific substantive prompts.",
    }


def journal_variant_audit(entries: list[dict[str, Any]]) -> dict[str, Any]:
    expected_variants = 12
    fields = ("journal_prayer_record", "journal_follow_through")
    results: dict[str, Any] = {}
    failures = []
    for field in fields:
        overall = Counter(normalize_text(entry[field]) for entry in entries)
        malformed = []
        for value in overall:
            word_count = len(words(value))
            if not value.endswith("?") or not value[:1].isupper() or not 6 <= word_count <= 20:
                malformed.append({"value": value, "words": word_count})
        by_volume = {}
        for volume in range(1, 4):
            counts = Counter(
                normalize_text(entry[field]) for entry in entries if entry["volume"] == volume
            )
            distribution = sorted(counts.values())
            volume_failures = []
            if len(counts) != expected_variants:
                volume_failures.append(
                    f"expected {expected_variants} variants, found {len(counts)}"
                )
            if distribution and (min(distribution) < 30 or max(distribution) > 31):
                volume_failures.append(
                    f"expected balanced 30/31 uses, found {min(distribution)}-{max(distribution)}"
                )
            by_volume[str(volume)] = {
                "unique_variants": len(counts),
                "minimum_uses": min(distribution, default=0),
                "maximum_uses": max(distribution, default=0),
                "failures": volume_failures,
            }
            failures.extend(f"{field} Volume {volume}: {reason}" for reason in volume_failures)
        if len(overall) != expected_variants:
            failures.append(
                f"{field}: expected {expected_variants} trilogy variants, found {len(overall)}"
            )
        if malformed:
            failures.append(f"{field}: {len(malformed)} malformed question variants")
        results[field] = {
            "expected_variants": expected_variants,
            "unique_variants": len(overall),
            "variants": [
                {"text": value, "uses": count}
                for value, count in sorted(overall.items())
            ],
            "malformed_variants": malformed,
            "by_volume": by_volume,
        }
    return {
        "method": "Prayer-record and follow-through must each provide exactly 12 grammatical question variants across the trilogy and within every volume. Each volume must distribute every variant evenly across 30 or 31 journal units.",
        "fields": results,
        "failures": failures,
        "pass": not failures,
    }


def grammar_audit(entries: list[dict[str, Any]]) -> dict[str, Any]:
    lowercase = []
    doubled = []
    missing_verb = []
    context_fragments = []
    title_flags = []
    long_title_review_candidates = []
    empty_fields = []
    short_closings = []
    response_contract = []
    severe_fragments = []
    for entry in entries:
        reasons = title_naturalness(entry)
        if reasons:
            title_flags.append({"entry_id": entry["id"], "title": entry["title"], "reasons": reasons})
        if len(words(entry["title"])) > 13:
            long_title_review_candidates.append({
                "entry_id": entry["id"], "title": entry["title"],
                "words": len(words(entry["title"])),
                "classification": "diagnostic read-aloud candidate; current locked judge reviewed all length-only candidates as grammatical",
            })
        for field in ("title", "scripture_reference", "scripture_text", "closing", "prayer", "reflection_and_response"):
            if not normalize_space(str(entry.get(field, ""))):
                empty_fields.append({"entry_id": entry["id"], "field": field})
        if not entry.get("body") or not normalize_space(" ".join(entry["body"])):
            empty_fields.append({"entry_id": entry["id"], "field": "body"})
        if len(words(entry["closing"])) < 6:
            short_closings.append({"entry_id": entry["id"], "closing": entry["closing"]})
        if "Then sit with this question:" not in entry["reflection_and_response"] or not entry["reflection_and_response"].rstrip().endswith("?"):
            response_contract.append({"entry_id": entry["id"], "response": entry["reflection_and_response"]})
        values = {
            "context": split_all_sentences(entry["context"]),
            "body": [
                sentence for paragraph in entry["body"]
                for sentence in split_all_sentences(paragraph)
            ],
            "closing": split_all_sentences(entry["closing"]),
            "prayer": split_all_sentences(entry["prayer"]),
            "response": split_all_sentences(entry["reflection_and_response"]),
            "journal_reflect": split_all_sentences(entry["journal_reflect"]),
            "journal_act": split_all_sentences(entry["journal_act"]),
        }
        for field, units in values.items():
            for unit in units:
                stripped = re.sub(r"^[`'\"(\[]+", "", unit.strip())
                if stripped and stripped[0].islower():
                    lowercase.append({"entry_id": entry["id"], "field": field, "text": unit[:260]})
                for match in re.finditer(r"\b([A-Za-z]+)\s+\1\b", unit, re.I):
                    doubled.append({"entry_id": entry["id"], "field": field, "text": match.group(0)})
                if MISSING_VERB_PATTERN.search(unit):
                    missing_verb.append({"entry_id": entry["id"], "field": field, "text": unit[:300]})
                if SCRIPTURE_INVITATION_FRAGMENT.search(stripped) and not SCRIPTURE_INVITATION_FINITE_VERB.search(stripped):
                    severe_fragments.append({
                        "entry_id": entry["id"], "field": field,
                        "reason": "orphaned Scripture-invitation fragment", "text": unit[:300],
                    })
                if MALFORMED_TEACH_ME_REST.search(stripped):
                    severe_fragments.append({
                        "entry_id": entry["id"], "field": field,
                        "reason": "malformed teach-me-rest construction", "text": unit[:300],
                    })
                for reason, pattern in SEVERE_FRAGMENT_PATTERNS:
                    if pattern.search(stripped):
                        severe_fragments.append({
                            "entry_id": entry["id"], "field": field,
                            "reason": reason, "text": unit[:300],
                        })
        if re.search(r"\bThis verse centers on (?:costly|love)\.$", entry["context"], re.I):
            context_fragments.append({"entry_id": entry["id"], "context": entry["context"]})
    scripture_invitation_fragments = [
        row for row in severe_fragments
        if row["reason"] == "orphaned Scripture-invitation fragment"
    ]
    teach_me_rest_fragments = [
        row for row in severe_fragments
        if row["reason"] == "malformed teach-me-rest construction"
    ]
    return {
        "empty_required_fields": empty_fields,
        "short_closing_candidates": short_closings,
        "response_contract_failures": response_contract,
        "lowercase_unit_starts": lowercase,
        "doubled_adjacent_words": doubled,
        "missing_verb_or_title_substitution_fragments": missing_verb,
        "malformed_context_fragments": context_fragments,
        "severe_sentence_fragments": severe_fragments,
        "scripture_invitation_fragment_failures": scripture_invitation_fragments,
        "malformed_teach_me_rest_failures": teach_me_rest_fragments,
        "title_naturalness_flags": title_flags,
        "long_title_review_candidates": long_title_review_candidates,
    }


def parse_index(text: str) -> list[dict[str, str]]:
    if "# Scripture Journey Index" not in text:
        return []
    section = text.split("# Scripture Journey Index", 1)[1]
    rows = []
    for line in section.splitlines():
        match = re.fullmatch(r"\| (.+?) \| (.+?) \| (.+?) \| (.+?) \|", line.strip())
        if not match or match.group(1) in {"Scripture", "---"}:
            continue
        if set(match.group(1)) == {"-"}:
            continue
        rows.append({
            "scripture_reference": match.group(1), "date": match.group(2),
            "day": match.group(3), "title": match.group(4),
        })
    return rows


def index_sort_key(reference: str) -> tuple[int, int, int]:
    parsed = parse_reference(reference)
    if not parsed:
        return 999, 999, 999
    return BOOK_ORDER.get(parsed[0], 999), parsed[1], parsed[2]


OPENBIBLE_GOSPEL_CODES = {
    "Matt": "Matthew", "Mark": "Mark", "Luke": "Luke", "John": "John",
}


def parse_openbible_reference(value: str) -> str:
    match = re.match(r"^([1-3]?[A-Za-z]+)\.(\d+)\.(\d+)", value)
    if not match or match.group(1) not in OPENBIBLE_GOSPEL_CODES:
        return ""
    return f"{OPENBIBLE_GOSPEL_CODES[match.group(1)]} {match.group(2)}:{match.group(3)}"


def load_openbible_graph() -> tuple[dict[tuple[str, str], int], dict[str, Any]]:
    graph: dict[tuple[str, str], int] = {}
    with zipfile.ZipFile(OPENBIBLE_ZIP) as archive:
        bad_member = archive.testzip()
        names = archive.namelist()
        if names != ["cross_references.txt"]:
            raise ValueError(f"Unexpected OpenBible archive members: {names}")
        lines = archive.read("cross_references.txt").decode("utf-8").splitlines()
    if not lines or "CC-BY" not in lines[0] or "From Verse" not in lines[0]:
        raise ValueError("OpenBible header or CC-BY marker is missing")
    parsed_rows = 0
    gospel_rows = 0
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        parsed_rows += 1
        left = parse_openbible_reference(parts[0])
        right = parse_openbible_reference(parts[1])
        if not left or not right or left == right:
            continue
        votes = int(parts[2])
        gospel_rows += 1
        graph[(left, right)] = max(votes, graph.get((left, right), -999))
        graph[(right, left)] = max(votes, graph.get((right, left), -999))
    return graph, {
        "archive_sha256": sha256(OPENBIBLE_ZIP),
        "archive_members": names,
        "zip_bad_member": bad_member,
        "data_rows": len(lines) - 1,
        "parsed_rows": parsed_rows,
        "gospel_rows": gospel_rows,
        "undirected_gospel_edges": len(graph) // 2,
        "header": lines[0],
    }


def semantic_words(value: str) -> set[str]:
    return {
        word.lower() for word in re.findall(r"[A-Za-z][A-Za-z']+", value)
        if len(word) >= 4 and word.lower() not in STOPWORDS
    }


def punctuation_free_key(value: str) -> str:
    return normalize_space(re.sub(r"[^A-Za-z0-9']+", " ", normalize_text(value))).lower()


def gospel_match_words(value: str) -> list[str]:
    return [
        word for word in re.findall(r"[a-z']+", value.lower())
        if len(word) > 2 and word not in GOSPEL_MATCH_STOPWORDS
    ]


def scripture_context_window(
    kjv: dict[tuple[str, int, int], str], reference: str, radius: int = 2,
) -> str:
    parsed = parse_reference(reference)
    if not parsed:
        return ""
    book, chapter, verse = parsed
    return " ".join(
        kjv.get((book, chapter, number), "")
        for number in range(max(1, verse - radius), verse + radius + 1)
    )


def audit_volume_2_cross_references(
    entries: list[dict[str, Any]],
    kjv: dict[tuple[str, int, int], str],
    graph: dict[tuple[str, str], int],
) -> dict[str, Any]:
    provenance_failures = []
    changed = []
    non_edges = []
    overlap_failures = []
    exact_source_quote_mismatches = []
    review_candidates = []
    for entry in entries:
        provenance = entry.get("source_provenance") or {}
        original = normalize_space(str(provenance.get("original_scripture", "")))
        current = entry.get("scripture_reference", "")
        original_parsed = parse_reference(original)
        current_parsed = parse_reference(current)
        if not original or not original_parsed or original_parsed not in kjv:
            provenance_failures.append({
                "entry_id": entry["id"], "kind": "missing_or_invalid_original_scripture",
                "value": original,
            })
            continue
        if original == current:
            continue
        votes = graph.get((original, current))
        row = {
            "entry_id": entry["id"], "day_number": entry["day_number"], "date": entry["date"],
            "title": entry["title"], "original": original, "current": current, "votes": votes,
        }
        source_text = normalize_text(kjv[original_parsed])
        current_text = normalize_text(kjv[current_parsed]) if current_parsed in kjv else ""
        source_words = gospel_match_words(source_text)
        current_words = gospel_match_words(current_text)
        source_window_words = gospel_match_words(scripture_context_window(kjv, original))
        current_window_words = gospel_match_words(scripture_context_window(kjv, current))
        verse_tokens = set(source_words).intersection(current_words)
        verse_bigrams = set(zip(source_words, source_words[1:])).intersection(
            zip(current_words, current_words[1:])
        )
        window_tokens = set(source_window_words).intersection(current_window_words)
        window_bigrams = set(zip(source_window_words, source_window_words[1:])).intersection(
            zip(current_window_words, current_window_words[1:])
        )
        row.update({
            "verse_token_overlap": len(verse_tokens),
            "verse_bigram_overlap": len(verse_bigrams),
            "context_window_radius": 2,
            "window_token_overlap": len(window_tokens),
            "window_bigram_overlap": len(window_bigrams),
        })
        changed.append(row)
        if votes is None:
            non_edges.append(row)
            continue
        if not verse_tokens or not window_tokens or not window_bigrams:
            overlap_failures.append({
                **row,
                "reason": "The direct edge lacks required same-verse token overlap or +/-2-verse window token/bigram overlap.",
            })

        prose = " ".join([
            entry.get("context", ""), *entry.get("body", []), entry.get("closing", ""),
            entry.get("prayer", ""), entry.get("reflection_and_response", ""),
        ])
        for quote in re.findall(r'[“"]([^”"]+)[”"]', prose):
            quote_normalized = normalize_text(quote)
            quote_key = punctuation_free_key(quote_normalized)
            if (
                len(words(quote_normalized)) >= 4
                and quote_key in punctuation_free_key(source_text)
                and quote_key not in punctuation_free_key(current_text)
            ):
                exact_source_quote_mismatches.append({
                    **row, "quoted_text": quote_normalized,
                    "source_text": source_text, "current_text": current_text,
                    "reason": "Prose reproduces an exact source-verse phrase that is absent from the reassigned primary verse.",
                })

        source_tokens = semantic_words(source_text)
        current_tokens = semantic_words(current_text)
        source_only = source_tokens - current_tokens
        current_only = current_tokens - source_tokens
        attributed_sentences = [
            sentence for sentence in split_sentences(prose)
            if current in sentence
        ]
        for sentence in attributed_sentences:
            sentence_tokens = semantic_words(sentence)
            source_hits = sorted(source_only & sentence_tokens)
            current_hits = sorted(current_only & sentence_tokens)
            if len(source_hits) >= 2 and not current_hits:
                review_candidates.append({
                    **row, "sentence": sentence, "source_only_terms": source_hits,
                    "source_text": source_text, "current_text": current_text,
                    "classification": "manual semantic review candidate; not an automatic proven failure",
                })
    broad_exclusion_failures = []
    rows_by_original: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        original = normalize_space(str((entry.get("source_provenance") or {}).get("original_scripture", "")))
        rows_by_original[original].append(entry)
    for original in sorted(EXCLUDED_BROAD_GOSPEL_SOURCES):
        source_rows = rows_by_original.get(original, [])
        if len(source_rows) != 1 or source_rows[0]["scripture_reference"] != original:
            broad_exclusion_failures.append({
                "original": original,
                "matching_rows": [
                    {"entry_id": entry["id"], "current": entry["scripture_reference"]}
                    for entry in source_rows
                ],
                "reason": "The declared broad mapping source was missing, duplicated, or reassigned.",
            })
    forced_original, forced_current = FORCED_GOSPEL_PARALLEL
    forced_rows = [row for row in changed if row["original"] == forced_original]
    forced_mapping_failures = []
    if len(forced_rows) != 1 or forced_rows[0]["current"] != forced_current:
        forced_mapping_failures.append({
            "expected": {"original": forced_original, "current": forced_current},
            "actual": forced_rows,
        })

    reviewed_mismatches = []
    reviewed_contextual_nonfailures = []
    review_configuration_failures = []
    candidates_by_id = {row["entry_id"]: row for row in review_candidates}
    changed_by_id = {row["entry_id"]: row for row in changed}
    entry_by_id = {entry["id"]: entry for entry in entries}
    for entry_id, expected in CURRENT_HASH_CONFIRMED_ATTRIBUTION_MISMATCHES.items():
        row = changed_by_id.get(entry_id)
        entry = entry_by_id.get(entry_id)
        prose = " ".join([entry.get("context", ""), *entry.get("body", [])]) if entry else ""
        if (
            not row or not entry
            or row["original"] != expected["original"]
            or row["current"] != expected["current"]
            or normalize_text(expected["claim"]) not in normalize_text(prose)
            or entry_id not in candidates_by_id
        ):
            review_configuration_failures.append({
                "entry_id": entry_id,
                "reason": "The hash-locked reviewed finding no longer matches the audited row or prose.",
            })
            continue
        original_parsed = parse_reference(row["original"])
        current_parsed = parse_reference(row["current"])
        reviewed_mismatches.append({
            **row, "claim": expected["claim"], "reason": expected["reason"],
            "source_text": kjv[original_parsed], "current_text": kjv[current_parsed],
            "classification": "confirmed current-hash verse-attribution mismatch",
        })
    for entry_id, expected in CURRENT_HASH_REVIEWED_CONTEXTUAL_NONFAILURES.items():
        row = changed_by_id.get(entry_id)
        entry = entry_by_id.get(entry_id)
        prose = " ".join([entry.get("context", ""), *entry.get("body", [])]) if entry else ""
        if (
            not row or not entry
            or row["original"] != expected["original"]
            or row["current"] != expected["current"]
            or normalize_text(expected["claim"]) not in normalize_text(prose)
            or entry_id not in candidates_by_id
        ):
            review_configuration_failures.append({
                "entry_id": entry_id,
                "reason": "The hash-locked reviewed contextual nonfailure no longer matches the audited row or prose.",
            })
            continue
        reviewed_contextual_nonfailures.append({
            **row, "claim": expected["claim"], "reason": expected["reason"],
            "classification": "reviewed immediate-context statement; not a failure",
        })
    proven_mismatches = exact_source_quote_mismatches + reviewed_mismatches
    reviewed_candidate_ids = {
        row["entry_id"]
        for row in exact_source_quote_mismatches + reviewed_mismatches + reviewed_contextual_nonfailures
    }
    unreviewed_semantic_candidates = [
        row for row in review_candidates if row["entry_id"] not in reviewed_candidate_ids
    ]
    votes = [row["votes"] for row in changed if row["votes"] is not None]
    return {
        "expected_reassignments": 150,
        "reassignments": len(changed),
        "provenance_failures": provenance_failures,
        "direct_edge_count": len(changed) - len(non_edges),
        "non_edges": non_edges,
        "context_window_radius": 2,
        "overlap_failures": overlap_failures,
        "overlap_summary": {
            "minimum_verse_token_overlap": min((row["verse_token_overlap"] for row in changed), default=None),
            "minimum_verse_bigram_overlap": min((row["verse_bigram_overlap"] for row in changed), default=None),
            "minimum_window_token_overlap": min((row["window_token_overlap"] for row in changed), default=None),
            "minimum_window_bigram_overlap": min((row["window_bigram_overlap"] for row in changed), default=None),
        },
        "target_book_counts": dict(Counter(
            (parse_reference(row["current"]) or ("INVALID", 0, 0))[0] for row in changed
        )),
        "broad_exclusions_checked": sorted(EXCLUDED_BROAD_GOSPEL_SOURCES),
        "broad_exclusion_failures": broad_exclusion_failures,
        "forced_parallel_expected": {"original": forced_original, "current": forced_current},
        "forced_parallel_rows": forced_rows,
        "forced_mapping_failures": forced_mapping_failures,
        "vote_summary": {
            "minimum": min(votes) if votes else None,
            "median": statistics.median(votes) if votes else None,
            "maximum": max(votes) if votes else None,
            "under_10": sum(vote < 10 for vote in votes),
        },
        "changed_rows": changed,
        "proven_semantic_source_mismatches": proven_mismatches,
        "review_configuration_failures": review_configuration_failures,
        "semantic_review_candidates": review_candidates,
        "reviewed_contextual_nonfailures": reviewed_contextual_nonfailures,
        "unreviewed_semantic_candidates": unreviewed_semantic_candidates,
    }


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = {"w": W_NS}


def entry_marker(entry: dict[str, Any]) -> str:
    if entry["day_number"] == 0:
        return "BONUS READING | FEBRUARY 29"
    return f"DAY {entry['day_number']:03d} | {entry['date'].upper()}"


def entry_page_key(entry: dict[str, Any]) -> str:
    return "bonus" if entry["day_number"] == 0 else f"day-{entry['day_number']:03d}"


def audit_docx(path: Path, entries: list[dict[str, Any]], kind: str) -> dict[str, Any]:
    mismatches = []
    with zipfile.ZipFile(path) as archive:
        bad_member = archive.testzip()
        names = archive.namelist()
        if "word/document.xml" not in names:
            raise ValueError(f"DOCX missing word/document.xml: {path}")
        root = ET.fromstring(archive.read("word/document.xml"))
    paragraphs = []
    for paragraph in root.findall(".//w:p", W):
        text = "".join(node.text or "" for node in paragraph.findall(".//w:t", W)).strip()
        if text:
            paragraphs.append(normalize_text(text))
    sections = []
    for section in root.findall(".//w:sectPr", W):
        page_size = section.find("w:pgSz", W)
        if page_size is None:
            sections.append({"width_twips": None, "height_twips": None})
        else:
            sections.append({
                "width_twips": int(page_size.get(f"{{{W_NS}}}w", "0")),
                "height_twips": int(page_size.get(f"{{{W_NS}}}h", "0")),
            })
    wrong_sections = [row for row in sections if row != {"width_twips": 8640, "height_twips": 12960}]

    marker_positions = [
        index for index, paragraph in enumerate(paragraphs)
        if re.fullmatch(r"(?:DAY \d{3}|BONUS READING)\s*\|\s*[A-Z]+ \d{1,2}", paragraph)
    ]
    if len(marker_positions) != 366:
        mismatches.append({"kind": "entry_marker_count", "actual": len(marker_positions), "expected": 366})
    for position, entry in enumerate(entries):
        if position >= len(marker_positions):
            mismatches.append({"entry_id": entry["id"], "kind": "missing_entry_block"})
            continue
        start = marker_positions[position]
        end = marker_positions[position + 1] if position + 1 < len(marker_positions) else len(paragraphs)
        block_paragraphs = paragraphs[start:end]
        block = normalize_text(" ".join(block_paragraphs))
        expected_fields = {
            "marker": entry_marker(entry),
            "title": entry["title"],
            "reference": f"{entry['scripture_reference']} | KJV",
            "scripture_text": entry["scripture_text"],
        }
        if kind == "reader":
            expected_fields.update({
                "closing": entry["closing"], "prayer": entry["prayer"],
                "response": entry["reflection_and_response"],
            })
        else:
            expected_fields.update({
                "observe": entry["journal_observe"], "reflect": entry["journal_reflect"],
                "act": entry["journal_act"], "prayer": entry["prayer"],
                "prayer_record": entry["journal_prayer_record"],
                "follow_through": entry["journal_follow_through"],
            })
        for field, expected_value in expected_fields.items():
            if normalize_text(expected_value) not in block:
                mismatches.append({
                    "entry_id": entry["id"], "kind": "field_sync", "field": field,
                    "expected": normalize_text(expected_value)[:360],
                })
        if kind == "journal":
            writing_lines = sum(bool(re.fullmatch(r"_{20,}", value)) for value in block_paragraphs)
            if writing_lines < 9:
                mismatches.append({
                    "entry_id": entry["id"], "kind": "writing_lines",
                    "actual": writing_lines, "minimum": 9,
                })
    return {
        "path": str(path.relative_to(REPO)), "sha256": sha256(path),
        "zip_bad_member": bad_member, "package_members": len(names),
        "sections": sections, "wrong_size_sections": wrong_sections,
        "paragraphs": len(paragraphs), "entry_blocks": len(marker_positions),
        "mismatches": mismatches,
    }


def run_text_command(arguments: list[str]) -> str:
    result = subprocess.run(arguments, check=True, capture_output=True)
    return result.stdout.decode("utf-8", errors="replace")


def normalize_pdf_text(value: str) -> str:
    value = normalize_text(value)
    return re.sub(r"(?<=[A-Za-z])\-\s+(?=[A-Za-z])", "-", value)


def audit_pdf(
    path: Path,
    entries: list[dict[str, Any]],
    kind: str,
    page_map: dict[str, int],
) -> dict[str, Any]:
    summary = run_text_command(["pdfinfo", str(path)])
    pages_match = re.search(r"^Pages:\s+(\d+)", summary, re.M)
    page_count = int(pages_match.group(1)) if pages_match else 0
    details = run_text_command(["pdfinfo", "-f", "1", "-l", str(page_count), str(path)])
    sizes = {
        int(number): (float(width), float(height))
        for number, width, height in re.findall(
            r"^Page\s+(\d+) size:\s+([0-9.]+) x ([0-9.]+) pts", details, re.M
        )
    }
    wrong_size_pages = [
        number for number in range(1, page_count + 1)
        if sizes.get(number) != (432.0, 648.0)
    ]
    raw_text = run_text_command(["pdftotext", "-layout", str(path), "-"])
    text_pages = raw_text.split("\f")
    if text_pages and not text_pages[-1].strip():
        text_pages.pop()
    blank_pages = [
        number for number, value in enumerate(text_pages, 1)
        if not re.search(r"[A-Za-z]", value)
    ]
    mismatches = []
    derived_page_map: dict[str, int] = {}
    marker_to_key = {normalize_pdf_text(entry_marker(entry)): entry_page_key(entry) for entry in entries}
    for page_number, raw_page in enumerate(text_pages, 1):
        page = normalize_pdf_text(raw_page)
        for marker, key in marker_to_key.items():
            if marker in page:
                if key in derived_page_map:
                    mismatches.append({
                        "entry_id": key, "kind": "duplicate_pdf_entry_marker",
                        "pages": [derived_page_map[key], page_number],
                    })
                derived_page_map[key] = page_number
    if set(derived_page_map) != set(marker_to_key.values()):
        mismatches.append({
            "kind": "derived_page_map_keys",
            "missing": sorted(set(marker_to_key.values()) - set(derived_page_map)),
            "extra": sorted(set(derived_page_map) - set(marker_to_key.values())),
        })
    if kind == "reader" and derived_page_map != page_map:
        mismatches.append({"kind": "builder_page_map_differs_from_independent_reader_map"})
    effective_page_map = page_map if kind == "reader" else derived_page_map
    for entry in entries:
        key = entry_page_key(entry)
        page_number = effective_page_map.get(key)
        if not isinstance(page_number, int) or not (1 <= page_number <= len(text_pages)):
            mismatches.append({"entry_id": entry["id"], "kind": "missing_or_invalid_page_map", "value": page_number})
            continue
        page = normalize_pdf_text(text_pages[page_number - 1])
        expected_fields = {
            "marker": entry_marker(entry), "title": entry["title"],
            "reference": f"{entry['scripture_reference']} | KJV",
            "scripture_text": entry["scripture_text"],
        }
        if kind == "reader":
            expected_fields["closing"] = entry["closing"]
        else:
            expected_fields.update({
                "observe": entry["journal_observe"], "reflect": entry["journal_reflect"],
                "act": entry["journal_act"],
            })
        for field, expected_value in expected_fields.items():
            if normalize_pdf_text(expected_value) not in page:
                mismatches.append({
                    "entry_id": entry["id"], "page": page_number,
                    "kind": "source_to_pdf_sync", "field": field,
                    "expected": normalize_pdf_text(expected_value)[:360],
                })

    index_result: dict[str, Any] | None = None
    if kind == "reader" and page_map:
        index_start = max(page_map.values()) + 1
        index_text = normalize_text(" ".join(text_pages[index_start - 1:]))
        row_mismatches = []
        title_mismatches = []
        reference_mismatches = []
        row_positions = []
        for entry in entries:
            day = "Bonus" if entry["day_number"] == 0 else f"Day {entry['day_number']}"
            page_number = page_map[entry_page_key(entry)]
            reference_title_pattern = re.compile(
                rf"{re.escape(entry['scripture_reference'])}\s+\|\s+{re.escape(entry['title'])}"
            )
            reference_title_match = reference_title_pattern.search(index_text)
            row_pattern = re.compile(
                rf"{re.escape(entry['scripture_reference'])}\s+\|\s+{re.escape(entry['title'])}\s+"
                rf"{re.escape(entry['date'])}\s+\|\s+{re.escape(day)}\s+\|\s+Page\s+{page_number}(?:\s|$)"
            )
            match = row_pattern.search(index_text)
            if not match:
                row_mismatches.append({
                    "entry_id": entry["id"], "reference": entry["scripture_reference"],
                    "date": entry["date"], "day": day, "page": page_number,
                })
            else:
                row_positions.append((entry, match.start()))
            if not reference_title_match:
                title_mismatches.append({"entry_id": entry["id"], "title": entry["title"]})
                reference_mismatches.append({
                    "entry_id": entry["id"], "reference": entry["scripture_reference"]
                })
        ordered_rows = sorted(row_positions, key=lambda row: row[1])
        actual_keys = [index_sort_key(entry["scripture_reference"]) for entry, _ in ordered_rows]
        order_inversions = []
        for position in range(1, len(ordered_rows)):
            previous = ordered_rows[position - 1][0]
            current = ordered_rows[position][0]
            if index_sort_key(current["scripture_reference"]) < index_sort_key(previous["scripture_reference"]):
                order_inversions.append({
                    "previous_entry_id": previous["id"],
                    "previous_reference": previous["scripture_reference"],
                    "current_entry_id": current["id"],
                    "current_reference": current["scripture_reference"],
                })
        index_result = {
            "start_page": index_start,
            "heading_present": "Scripture Journey Index" in index_text,
            "rows_verified": len(entries) - len(row_mismatches),
            "row_mismatches": row_mismatches,
            "titles_present": len(entries) - len(title_mismatches),
            "title_mismatches": title_mismatches,
            "references_present": len(entries) - len(reference_mismatches),
            "reference_mismatches": reference_mismatches,
            "row_format": "Passage | Full Title; Date | Day N/Bonus | Page N",
            "biblical_order_pass": not order_inversions,
            "order_inversions": order_inversions,
        }
    return {
        "path": str(path.relative_to(REPO)), "sha256": sha256(path),
        "pages": page_count, "text_pages": len(text_pages),
        "wrong_size_pages": wrong_size_pages, "blank_pages": blank_pages,
        "mapped_entries": len(derived_page_map), "derived_page_map": derived_page_map,
        "mismatches": mismatches,
        "scripture_index": index_result,
    }


def audit_interior_zip(required_names: list[str]) -> dict[str, Any]:
    missing_members = []
    extra_members = []
    byte_mismatches = []
    with zipfile.ZipFile(INTERIOR_ZIP) as archive:
        bad_member = archive.testzip()
        names = archive.namelist()
        missing_members = sorted(set(required_names) - set(names))
        extra_members = sorted(set(names) - set(required_names))
        for name in required_names:
            path = INTERIORS / name
            if name in names and path.exists() and archive.read(name) != path.read_bytes():
                byte_mismatches.append(name)
    return {
        "path": str(INTERIOR_ZIP.relative_to(REPO)), "sha256": sha256(INTERIOR_ZIP),
        "zip_bad_member": bad_member, "members": names,
        "missing_members": missing_members, "extra_members": extra_members,
        "byte_mismatches": byte_mismatches,
    }


def main() -> None:
    if not shutil.which("pdfinfo") or not shutil.which("pdftotext"):
        raise RuntimeError("pdfinfo and pdftotext are required for the independent PDF audit")
    interior_names = []
    for volume in range(1, 4):
        interior_names.extend([
            f"volume-{volume}-revised-reader-edition-6x9.docx",
            f"volume-{volume}-revised-reader-edition-6x9.pdf",
            f"volume-{volume}-revised-companion-journal-6x9.docx",
            f"volume-{volume}-revised-companion-journal-6x9.pdf",
        ])
    interior_names.append(INTERIOR_BUILD_AUDIT.name)
    required = [
        CONTRACT, KJV_ZIP, OPENBIBLE_ZIP, OPENBIBLE_LICENSE,
        INTERIOR_BUILD_AUDIT, INTERIOR_ZIP, VISUAL_REVIEW, JUDGE_REVIEW,
        *(INTERIORS / name for name in interior_names[:-1]),
    ]
    core_paths = []
    for volume in range(1, 4):
        base = CORPUS / f"volume-{volume}"
        paths = [
            base / f"volume-{volume}-reader-edition.json",
            base / f"volume-{volume}-reader-edition.md",
            base / f"volume-{volume}-companion-journal.md",
        ]
        required.extend(paths)
        core_paths.extend(paths)
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required audit inputs:\n" + "\n".join(missing))

    actual_hashes = {
        volume: sha256(CORPUS / f"volume-{volume}" / f"volume-{volume}-reader-edition.json")
        for volume in range(1, 4)
    }
    if actual_hashes != EXPECTED_JSON_HASHES:
        raise RuntimeError(
            "Hash lock mismatch; refusing to audit a different corpus.\n"
            f"expected={json.dumps(EXPECTED_JSON_HASHES, sort_keys=True)}\n"
            f"actual={json.dumps(actual_hashes, sort_keys=True)}"
        )
    actual_interior_zip_hash = sha256(INTERIOR_ZIP)
    if actual_interior_zip_hash != EXPECTED_INTERIOR_ZIP_HASH:
        raise RuntimeError(
            "Interior ZIP hash mismatch; refusing to audit a different production bundle.\n"
            f"expected={EXPECTED_INTERIOR_ZIP_HASH}\nactual={actual_interior_zip_hash}"
        )

    source_hashes = {"kjv": sha256(KJV_ZIP), "openbible": sha256(OPENBIBLE_ZIP)}
    expected_source_hashes = {"kjv": EXPECTED_KJV_HASH, "openbible": EXPECTED_OPENBIBLE_HASH}
    if source_hashes != expected_source_hashes:
        raise RuntimeError(
            "Scripture source hash mismatch; refusing to audit against changed or unverified source archives.\n"
            f"expected={json.dumps(expected_source_hashes, sort_keys=True)}\n"
            f"actual={json.dumps(source_hashes, sort_keys=True)}"
        )

    core_paths.extend([
        KJV_ZIP, OPENBIBLE_ZIP, OPENBIBLE_LICENSE, INTERIOR_BUILD_AUDIT,
        INTERIOR_ZIP, VISUAL_REVIEW, JUDGE_REVIEW,
    ])
    core_paths.extend(INTERIORS / name for name in interior_names[:-1])
    inventory = [{
        "path": str(path.relative_to(REPO)), "bytes": path.stat().st_size,
        "mtime_epoch": int(path.stat().st_mtime), "sha256": sha256(path),
    } for path in sorted(core_paths)]
    visual_review_evidence = audit_visual_review_evidence()
    kjv, kjv_meta = load_kjv()
    openbible_graph, openbible_meta = load_openbible_graph()
    license_text = OPENBIBLE_LICENSE.read_text(encoding="utf-8")
    openbible_meta["license_path"] = str(OPENBIBLE_LICENSE.relative_to(REPO))
    openbible_meta["license_sha256"] = sha256(OPENBIBLE_LICENSE)
    openbible_meta["license_checks"] = {
        "cc_attribution_present": bool(re.search(r"Creative Commons Attribution|CC[- ]BY", normalize_space(license_text), re.I)),
        "source_url_present": "https://www.openbible.info/labs/cross-references/" in license_text,
        "archive_hash_present": EXPECTED_OPENBIBLE_HASH in license_text,
    }
    expected = expected_dates()

    all_entries: list[dict[str, Any]] = []
    entries_by_volume: dict[int, list[dict[str, Any]]] = {}
    volume_results: dict[str, Any] = {}
    count_date_failures = []
    reference_failures = []
    kjv_mismatches = []
    reader_mismatches = []
    journal_mismatches = []
    index_mismatches = []
    calendar_hits = []
    internal_hits = []
    reader_meta_hits = []
    original_language_body = []
    context_contract_failures = []
    nonempty_optional_connections = []
    rendered_connection_labels = []
    provenance_failures = []
    deprecated_hits: dict[str, list[dict[str, str]]] = {label: [] for label in DEPRECATED_LABELS}

    for volume in range(1, 4):
        entries_by_volume[volume] = []
        base = CORPUS / f"volume-{volume}"
        json_path = base / f"volume-{volume}-reader-edition.json"
        reader_path = base / f"volume-{volume}-reader-edition.md"
        journal_path = base / f"volume-{volume}-companion-journal.md"
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        entries = payload.get("entries", [])
        reader_text = reader_path.read_text(encoding="utf-8")
        journal_text = journal_path.read_text(encoding="utf-8")
        reader_blocks = parse_daily_blocks(reader_text)
        journal_blocks = parse_daily_blocks(journal_text)
        themes = payload.get("themes", [])

        for label in DEPRECATED_LABELS:
            if re.search(re.escape(label), reader_text, re.I):
                deprecated_hits[label].append({"entry_id": f"V{volume}-reader", "source": "reader Markdown"})
            if re.search(re.escape(label), journal_text, re.I):
                deprecated_hits[label].append({"entry_id": f"V{volume}-journal", "source": "journal Markdown"})

        if len(entries) != 366:
            count_date_failures.append({"volume": volume, "kind": "json_entry_count", "actual": len(entries), "expected": 366})
        if len(reader_blocks) != 366:
            count_date_failures.append({"volume": volume, "kind": "reader_block_count", "actual": len(reader_blocks), "expected": 366})
        if len(journal_blocks) != 366:
            count_date_failures.append({"volume": volume, "kind": "journal_block_count", "actual": len(journal_blocks), "expected": 366})

        for index, raw in enumerate(entries):
            entry = dict(raw)
            entry["volume"] = volume
            entry["id"] = f"V{volume}-{'bonus' if entry.get('day_number') == 0 else f'D{entry.get('day_number', -1):03d}'}"
            month_index = MONTHS.index(entry["date"].split()[0]) if entry.get("date") else 0
            entry["theme_name"] = themes[month_index].get("name", "") if month_index < len(themes) else ""
            entry["theme_promise"] = themes[month_index].get("promise", "") if month_index < len(themes) else ""
            all_entries.append(entry)
            entries_by_volume[volume].append(entry)

            provenance = entry.get("source_provenance") or {}
            original_scripture = normalize_space(str(provenance.get("original_scripture", "")))
            original_parsed = parse_reference(original_scripture)
            if not original_scripture or not original_parsed or original_parsed not in kjv:
                provenance_failures.append({
                    "entry_id": entry["id"], "kind": "missing_or_invalid_original_scripture",
                    "value": original_scripture,
                })

            if index >= len(expected) or (entry.get("day_number"), entry.get("date")) != expected[index]:
                count_date_failures.append({
                    "entry_id": entry["id"], "position": index,
                    "actual": [entry.get("day_number"), entry.get("date")],
                    "expected": list(expected[index]) if index < len(expected) else None,
                })

            if entry.get("scripture_translation") != "KJV":
                reference_failures.append({"entry_id": entry["id"], "kind": "translation", "actual": entry.get("scripture_translation")})
            parsed = parse_reference(entry.get("scripture_reference", ""))
            if not parsed or parsed not in kjv:
                reference_failures.append({"entry_id": entry["id"], "kind": "reference", "reference": entry.get("scripture_reference", "")})
            elif normalize_text(entry.get("scripture_text", "")) != kjv[parsed]:
                kjv_mismatches.append({
                    "entry_id": entry["id"], "reference": entry["scripture_reference"],
                    "actual": normalize_text(entry.get("scripture_text", "")), "oracle": kjv[parsed],
                })

            if entry.get("scripture_connection_reference") or entry.get("scripture_connection_text"):
                nonempty_optional_connections.append({
                    "entry_id": entry["id"],
                    "reference": entry.get("scripture_connection_reference", ""),
                    "text": entry.get("scripture_connection_text", ""),
                })

            reader_block = reader_blocks.get(entry["date"], "")
            reader_expected = {
                "title": f"### {entry['title']}",
                "reference": f"**Scripture: {entry['scripture_reference']} (KJV)**",
                "scripture_text": f"> {entry['scripture_text']}",
                "closing": entry["closing"], "prayer": f"**Prayer:** {entry['prayer']}",
                "response": f"**Reflect and respond:** {entry['reflection_and_response']}",
            }
            reader_expected.update({f"body_{position}": paragraph for position, paragraph in enumerate(entry["body"])})
            if entry["context"]:
                reader_expected["context"] = f"**{entry['context_label']}:** {entry['context']}"
            for field, value in reader_expected.items():
                if value and not md_contains(reader_block, value):
                    reader_mismatches.append({"entry_id": entry["id"], "field": field, "expected": value[:320]})
            if "**Scripture connection:" in reader_block:
                rendered_connection_labels.append({"entry_id": entry["id"]})

            journal_block = journal_blocks.get(entry["date"], "")
            journal_expected = {
                "title": f"### {entry['title']}",
                "reference": f"**Return to the Word:** {entry['scripture_reference']} (KJV)",
                "scripture_text": f"> {entry['scripture_text']}",
                "observe": f"**Observe:** {entry['journal_observe']}",
                "reflect": f"**Reflect:** {entry['journal_reflect']}",
                "act": f"**Act:** {entry['journal_act']}",
                "prayer": f"**Prayer starter:** {entry['prayer']}",
                "prayer_record": f"**Prayer record:** {entry['journal_prayer_record']}",
                "follow_through": f"**Follow-through:** {entry['journal_follow_through']}",
                "write": "**Write:**",
            }
            for field, value in journal_expected.items():
                if value and not md_contains(journal_block, value):
                    journal_mismatches.append({"entry_id": entry["id"], "field": field, "expected": value[:320]})
            writing_lines = len(re.findall(r"^_{20,}\s*$", journal_block, re.M))
            if writing_lines != 9:
                journal_mismatches.append({"entry_id": entry["id"], "field": "writing_lines", "actual": writing_lines, "expected": 9})

            entry_text = " ".join([
                entry["title"], entry["context"], *entry["body"], entry["closing"],
                entry["prayer"], entry["reflection_and_response"], entry["journal_observe"],
                entry["journal_reflect"], entry["journal_act"], entry["journal_prayer_record"],
                entry["journal_follow_through"],
            ])
            for label in DEPRECATED_LABELS:
                if re.search(re.escape(label), entry_text, re.I):
                    deprecated_hits[label].append({"entry_id": entry["id"], "source": "JSON entry content"})
            if CALENDAR_PATTERN.search(entry_text):
                calendar_hits.append({
                    "entry_id": entry["id"], "matches": CALENDAR_PATTERN.findall(entry_text),
                    "excerpts": matching_excerpts(entry_text, CALENDAR_PATTERN),
                })
            if INTERNAL_PATTERN.search(entry_text):
                internal_hits.append({
                    "entry_id": entry["id"], "matches": INTERNAL_PATTERN.findall(entry_text),
                    "excerpts": matching_excerpts(entry_text, INTERNAL_PATTERN),
                })
            if READER_META_PATTERN.search(entry_text):
                reader_meta_hits.append({"entry_id": entry["id"], "matches": READER_META_PATTERN.findall(entry_text)})
            body_roots = sorted(set(match.group(0) for match in ROOT_CORE.finditer(" ".join(entry["body"]))))
            if body_roots:
                original_language_body.append({"entry_id": entry["id"], "terms": body_roots})
            context_has_root = bool(ROOT_CORE.search(entry["context"]))
            if entry["context_label"] not in {"Scripture context", "Word and context"}:
                context_contract_failures.append({"entry_id": entry["id"], "reason": "unapproved context label", "label": entry["context_label"]})
            elif entry["context"] and entry["context_label"] == "Word and context" and not context_has_root:
                context_contract_failures.append({"entry_id": entry["id"], "reason": "word label without root signal"})
            elif entry["context"] and entry["context_label"] == "Scripture context" and context_has_root:
                context_contract_failures.append({"entry_id": entry["id"], "reason": "root-language signal under Scripture context label"})
            if entry["context"].count("`") % 2:
                context_contract_failures.append({"entry_id": entry["id"], "reason": "unbalanced backticks"})

        month_reviews = re.findall(r"^## ([A-Za-z]+) Review\s*$", journal_text, re.M)
        missing_reviews = [month for month in MONTHS if month not in month_reviews]
        duplicate_reviews = [month for month, count in Counter(month_reviews).items() if count != 1]
        if missing_reviews or duplicate_reviews or len(month_reviews) != 12:
            journal_mismatches.append({
                "volume": volume, "field": "monthly_reviews", "actual_count": len(month_reviews),
                "missing": missing_reviews, "duplicates": duplicate_reviews,
            })

        index_rows = parse_index(reader_text)
        if len(index_rows) != 366:
            index_mismatches.append({"volume": volume, "kind": "index_count", "actual": len(index_rows), "expected": 366})
        expected_index = {
            (entry["scripture_reference"], entry["date"], "Bonus" if entry["day_number"] == 0 else str(entry["day_number"]), entry["title"])
            for entry in entries
        }
        actual_index = {(row["scripture_reference"], row["date"], row["day"], row["title"]) for row in index_rows}
        missing_index_rows = sorted(expected_index - actual_index)[:100]
        extra_index_rows = sorted(actual_index - expected_index)[:100]
        if missing_index_rows or extra_index_rows:
            index_mismatches.append({
                "volume": volume, "kind": "index_content", "missing": missing_index_rows,
                "extra": extra_index_rows,
            })
        if [index_sort_key(row["scripture_reference"]) for row in index_rows] != sorted(index_sort_key(row["scripture_reference"]) for row in index_rows):
            index_mismatches.append({"volume": volume, "kind": "index_not_in_biblical_order"})

        volume_entries = [entry for entry in all_entries if entry["volume"] == volume]
        body_counts = [len(words(" ".join(entry["body"]))) for entry in volume_entries]
        volume_results[str(volume)] = {
            "title": VOLUME_TITLES[volume], "entries": len(volume_entries),
            "dated_entries": sum(entry["day_number"] != 0 for entry in volume_entries),
            "bonus_entries": sum(entry["day_number"] == 0 for entry in volume_entries),
            "body_words": {
                "minimum": min(body_counts), "average": round(statistics.mean(body_counts), 1),
                "maximum": max(body_counts), "below_120": sum(count < 120 for count in body_counts),
            },
            "context_present": sum(bool(entry["context"]) for entry in volume_entries),
            "context_labels": dict(Counter(entry["context_label"] for entry in volume_entries)),
            "monthly_reviews": len(month_reviews), "index_rows": len(index_rows),
            "sequence": sequence_metrics(volume_entries),
        }

    volume_2_cross_references = audit_volume_2_cross_references(
        entries_by_volume[2], kjv, openbible_graph
    )

    build_audit_payload = json.loads(INTERIOR_BUILD_AUDIT.read_text(encoding="utf-8"))
    build_books = {int(row.get("volume", 0)): row for row in build_audit_payload.get("books", [])}
    build_audit_mismatches = []
    interior_results: dict[str, Any] = {}
    for volume in range(1, 4):
        entries = entries_by_volume[volume]
        build_book = build_books.get(volume, {})
        page_map = build_book.get("page_map", {})
        expected_keys = {entry_page_key(entry) for entry in entries}
        if set(page_map) != expected_keys:
            build_audit_mismatches.append({
                "volume": volume, "kind": "page_map_keys",
                "missing": sorted(expected_keys - set(page_map)),
                "extra": sorted(set(page_map) - expected_keys),
            })
        if build_book.get("entries") != 366 or build_book.get("mapped_entry_pages") != 366:
            build_audit_mismatches.append({
                "volume": volume, "kind": "entry_counts",
                "entries": build_book.get("entries"),
                "mapped_entry_pages": build_book.get("mapped_entry_pages"),
            })
        volume_artifacts = {}
        for kind, stem in (
            ("reader", f"volume-{volume}-revised-reader-edition-6x9"),
            ("journal", f"volume-{volume}-revised-companion-journal-6x9"),
        ):
            docx_result = audit_docx(INTERIORS / f"{stem}.docx", entries, kind)
            pdf_result = audit_pdf(INTERIORS / f"{stem}.pdf", entries, kind, page_map)
            volume_artifacts[kind] = {"docx": docx_result, "pdf": pdf_result}
            claim = build_book.get("devotional" if kind == "reader" else "journal", {})
            if claim.get("pages") != pdf_result["pages"]:
                build_audit_mismatches.append({
                    "volume": volume, "kind": kind, "field": "pages",
                    "claimed": claim.get("pages"), "independent": pdf_result["pages"],
                })
            if claim.get("wrong_size_pages", []) != pdf_result["wrong_size_pages"]:
                build_audit_mismatches.append({
                    "volume": volume, "kind": kind, "field": "wrong_size_pages",
                    "claimed": claim.get("wrong_size_pages", []),
                    "independent": pdf_result["wrong_size_pages"],
                })
            if claim.get("blank_pages", []) != pdf_result["blank_pages"]:
                build_audit_mismatches.append({
                    "volume": volume, "kind": kind, "field": "blank_pages",
                    "claimed": claim.get("blank_pages", []),
                    "independent": pdf_result["blank_pages"],
                })
        interior_results[str(volume)] = volume_artifacts

    interior_zip = audit_interior_zip(interior_names)
    grammar = grammar_audit(all_entries)
    repetition = repetition_audit(all_entries)
    removal_claims = removal_claim_audit(all_entries)
    deepening_scaffold = deepening_scaffold_audit(all_entries)
    reader_hygiene = reader_facing_hygiene_audit(all_entries)
    generated_templates = severe_generated_template_audit(all_entries)
    journal_repeat = journal_repetition(all_entries)
    journal_variants = journal_variant_audit(all_entries)
    exact_titles_by_volume = {
        str(volume): duplicate_summary((entry["id"], entry["title"]) for entry in all_entries if entry["volume"] == volume)
        for volume in range(1, 4)
    }
    cross_volume_titles = duplicate_summary((entry["id"], entry["title"]) for entry in all_entries)
    near_titles = near_title_pairs(all_entries)
    title_factory = title_factory_audit(all_entries)
    meaningful_title_word_repetitions = repeated_meaningful_title_words(all_entries)
    judge_remediation = judge_remediation_audit(all_entries)
    neither_remediation = auditor_neither_remediation_audit(all_entries)

    mismatch_categories = Counter()
    for row in kjv_mismatches:
        if row["actual"].startswith(row["oracle"]) and row["actual"] != row["oracle"]:
            mismatch_categories["appended_nonverse_material"] += 1
        elif re.sub(r"\s+([,.;:?!])", r"\1", row["actual"]) == row["oracle"]:
            mismatch_categories["space_before_punctuation"] += 1
        else:
            mismatch_categories["other_text_difference"] += 1
    plural_psalm_references = []
    for entry in all_entries:
        values = {"primary_reference": entry["scripture_reference"], **reader_facing_values(entry)}
        for field, value in values.items():
            for match in re.finditer(r"\bPsalms\s+\d+:\d+\b", value):
                plural_psalm_references.append({
                    "entry_id": entry["id"], "field": field,
                    "reference": match.group(0),
                    "reason": "Reader-facing Bible-book name must be singular Psalm.",
                })

    no_deprecated = not any(deprecated_hits.values())
    sequence_pass = all(
        not result["sequence"]["runs_over_7"]
        and not result["sequence"]["months_over_85_percent_one_book"]
        and not result["sequence"]["months_under_2_books"]
        and result["sequence"]["adjacent_same_book_rate"] <= 0.35
        for result in volume_results.values()
    )
    title_pass = (
        all(summary["duplicate_groups"] == 0 for summary in exact_titles_by_volume.values())
        and not grammar["title_naturalness_flags"]
        and not title_factory["volumes_with_factory_pattern"]
        and all(row["pass"] for row in judge_remediation["reviewed_title_rows"])
        and judge_remediation["verified_source_sha256"] == EXPECTED_JUDGE_REVIEW_HASH
    )
    grammar_pass = not any([
        grammar["empty_required_fields"], grammar["short_closing_candidates"],
        grammar["response_contract_failures"], grammar["lowercase_unit_starts"],
        grammar["doubled_adjacent_words"], grammar["missing_verb_or_title_substitution_fragments"],
        grammar["malformed_context_fragments"], grammar["severe_sentence_fragments"],
    ]) and all(row["pass"] for row in judge_remediation["detached_prose_rows"]) \
        and all(row["pass"] for row in judge_remediation["grammar_remediation_rows"]) \
        and neither_remediation["pass"]
    repetition_pass = (
        repetition["maximum_exact_sentence_reuse"] <= 3
        and repetition["masked_template_groups_over_3"] == 0
        and repetition["within_entry_duplicate_sentences"] == 0
        and journal_repeat["substantive_severe_group_count"] == 0
        and removal_claims["all_claimed_phrases_absent"]
        and deepening_scaffold["pass"]
        and generated_templates["pass"]
    )
    journal_pass = not journal_mismatches and journal_variants["pass"]
    license_pass = all(openbible_meta["license_checks"].values()) and openbible_meta["zip_bad_member"] is None
    cross_reference_pass = (
        not provenance_failures
        and volume_2_cross_references["reassignments"] == volume_2_cross_references["expected_reassignments"]
        and not volume_2_cross_references["provenance_failures"]
        and not volume_2_cross_references["review_configuration_failures"]
        and not volume_2_cross_references["non_edges"]
        and not volume_2_cross_references["overlap_failures"]
        and not volume_2_cross_references["broad_exclusion_failures"]
        and not volume_2_cross_references["forced_mapping_failures"]
        and not volume_2_cross_references["unreviewed_semantic_candidates"]
        and not volume_2_cross_references["proven_semantic_source_mismatches"]
        and license_pass
    )
    gates = [
        {"id": "G01", "name": "Corpus counts, dates, leap day, and Markdown index", "weight": 8, "pass": not count_date_failures and not index_mismatches},
        {"id": "G02", "name": "Exact primary KJV concordance and reader-facing reference naming", "weight": 14, "pass": not reference_failures and not kjv_mismatches and not plural_psalm_references},
        {"id": "G03", "name": "JSON-to-reader Markdown integrity", "weight": 8, "pass": not reader_mismatches},
        {"id": "G04", "name": "One-Scripture schema and current labels", "weight": 6, "pass": not rendered_connection_labels and no_deprecated},
        {"id": "G05", "name": "Evergreen calendar, Sabbath placement, legacy-label, and unsupported-claim hygiene", "weight": 7, "pass": not calendar_hits and not internal_hits and reader_hygiene["pass"]},
        {"id": "G06", "name": "Unique, natural titles within each volume", "weight": 8, "pass": title_pass},
        {"id": "G07", "name": "Body, closing, prayer, response, and grammar", "weight": 14, "pass": grammar_pass},
        {"id": "G08", "name": "No severe repeated devotional or substantive journal templates", "weight": 8, "pass": repetition_pass},
        {"id": "G09", "name": "Original-language placement and context contract", "weight": 5, "pass": not original_language_body and not context_contract_failures},
        {"id": "G10", "name": "Journal fields, one-to-one mapping, prompt variants, monthly reviews, and nine lines", "weight": 8, "pass": journal_pass},
        {"id": "G11", "name": "Non-mechanical primary Scripture journey", "weight": 6, "pass": sequence_pass},
        {"id": "G12", "name": "Provenance and documented Gospel-parallel fidelity", "weight": 8, "pass": cross_reference_pass},
    ]
    editorial_score = sum(gate["weight"] for gate in gates if gate["pass"])
    mandatory_failures = [gate for gate in gates if not gate["pass"]]
    score_gate_pass = editorial_score >= 88
    manuscript_verdict = "PASS" if not mandatory_failures and score_gate_pass else "FAIL"

    artifact_failures = []
    if build_audit_mismatches:
        artifact_failures.append(f"interior build-audit discrepancies: {len(build_audit_mismatches)}")
    for volume, artifacts in interior_results.items():
        for kind, pair in artifacts.items():
            docx = pair["docx"]
            pdf = pair["pdf"]
            expected_pages = 395 if kind == "reader" else 393
            if docx["zip_bad_member"] or docx["wrong_size_sections"] or docx["mismatches"]:
                artifact_failures.append(f"Volume {volume} {kind} DOCX failed independent package/size/source checks")
            if (
                pdf["pages"] != expected_pages or pdf["text_pages"] != expected_pages
                or pdf["wrong_size_pages"] or pdf["blank_pages"] or pdf["mismatches"]
            ):
                artifact_failures.append(f"Volume {volume} {kind} PDF failed page/size/blank/source checks")
            index = pdf.get("scripture_index")
            if kind == "reader" and (
                not index or not index["heading_present"] or index["row_mismatches"]
                or index["title_mismatches"] or not index["biblical_order_pass"]
            ):
                artifact_failures.append(f"Volume {volume} reader PDF Scripture Journey Index failed")
    if (
        interior_zip["zip_bad_member"] or interior_zip["missing_members"]
        or interior_zip["extra_members"] or interior_zip["byte_mismatches"]
    ):
        artifact_failures.append("interior ZIP integrity or current-file identity failed")
    artifact_verdict = "PASS" if not artifact_failures else "FAIL"

    production_proof = {
        "automated_rendered_page_checks": artifact_verdict == "PASS",
        "human_rendered_page_visual_approval_evidenced": visual_review_evidence["valid_for_local_human_rendered_page_flag"],
        "local_rendered_page_visual_evidence": visual_review_evidence,
        "final_author_visual_approval_evidenced": False,
        "kdp_previewer_evidenced": False,
        "physical_proof_approval_evidenced": False,
        "status": "PARTIAL - LOCAL RENDERED-PAGE REVIEW PASSED" if visual_review_evidence["valid_for_local_human_rendered_page_flag"] else "NOT COMPLETE",
        "note": (
            "The locked representative local rendered-page review supports only the local visual-evidence flag. It is not final author approval and does not replace KDP Previewer evidence or an approved physical proof."
            if visual_review_evidence["valid_for_local_human_rendered_page_flag"]
            else "The available local visual-review record predates this grammar freeze and rebuilt interior ZIP, so it is not accepted as visual evidence for the current artifacts."
        ),
    }
    release_verdict = "HOLD"

    manuscript_blocking_reasons = [f"{gate['id']} failed: {gate['name']}" for gate in mandatory_failures]
    if not score_gate_pass:
        manuscript_blocking_reasons.append(f"Independent editorial score is {editorial_score}/100, below the binding 88/100 minimum.")
    release_blocking_reasons = []
    if manuscript_verdict != "PASS":
        release_blocking_reasons.append("The manuscript gate has not passed.")
    if artifact_verdict != "PASS":
        release_blocking_reasons.append("The production-interior artifact gate has not passed.")
    if not visual_review_evidence["valid_for_local_human_rendered_page_flag"]:
        release_blocking_reasons.append("Local human rendered-page visual evidence is not validated.")
    release_blocking_reasons.extend([
        "Final author visual approval is not evidenced.",
        "KDP Previewer approval is not evidenced.",
        "Physical-proof approval is not evidenced.",
    ])

    report = {
        "audit_metadata": {
            "name": "Lady D Trilogy Independent Current-Schema Post-Rewrite Audit",
            "generated_at_utc": datetime.fromtimestamp(
                max(row["mtime_epoch"] for row in inventory), timezone.utc
            ).isoformat(),
            "methodology_version": "6.7.0-final-deepening-order-freeze",
            "verdict": release_verdict, "release_approved": False,
            "restart_statement": "All prior and interrupted audit findings were discarded. This report was recomputed only from the final hash-locked corpus listed here.",
            "contract_path": str(CONTRACT.relative_to(REPO)), "contract_sha256": sha256(CONTRACT),
            "expected_json_hashes": EXPECTED_JSON_HASHES, "verified_json_hashes": actual_hashes,
            "expected_interior_zip_hash": EXPECTED_INTERIOR_ZIP_HASH,
            "verified_interior_zip_hash": actual_interior_zip_hash,
            "expected_judge_checklist_hash": EXPECTED_JUDGE_REVIEW_HASH,
            "verified_judge_checklist_hash": judge_remediation["verified_source_sha256"],
            "expected_source_hashes": expected_source_hashes, "verified_source_hashes": source_hashes,
        },
        "scope": {
            "volumes": 3, "devotional_entries": len(all_entries),
            "journal_units": sum(result["entries"] for result in volume_results.values()),
            "primary_scriptures_checked": len(all_entries),
            "nonempty_optional_second_scriptures": len(nonempty_optional_connections),
            "core_manuscript_files_hashed": len(inventory),
            "docx_outputs_checked": 6, "pdf_outputs_checked": 6,
            "pdf_pages_checked": sum(
                pair["pdf"]["pages"]
                for artifacts in interior_results.values() for pair in artifacts.values()
            ),
            "volume_2_reassignments_checked": volume_2_cross_references["reassignments"],
            "judge_title_rows_rechecked": judge_remediation["reviewed_title_count"],
            "judge_detached_prose_rows_rechecked": judge_remediation["detached_prose_count"],
            "judge_grammar_rows_rechecked": judge_remediation["grammar_remediation_count"],
            "auditor_neither_rows_rechecked": neither_remediation["configured_rows"],
        },
        "input_inventory": inventory,
        "methodology": {
            "schema": "One required primary Scripture. Second Scripture fields may exist as empty compatibility keys and are not required or scored.",
            "independence": "JSON, Markdown, DOCX XML, PDF text/pages, KJV USFM, and OpenBible edges were parsed independently. The builder audit was compared with independent PDF results, not accepted as proof.",
            "sequence_gate": "Contract anti-crawl screen per volume: adjacent same-book rate <=35%, no same-book run >7 dated readings, every month >=2 books, no month >85% one book. Broader 40%/four-book diversity metrics remain diagnostic only.",
            "repetition_gate": "No exact reader sentence in >3 entries; no substantive title/reference/theme-masked sentence template in >3 entries; no within-entry duplicate sentence; no substantive journal Reflect/Act prompt in >3 entries; no colon-led generated frame in more than 30 entries; all specifically claimed removed production phrases must be absent; and every detected deepening scaffold must be reserved for a preceding body under 100 words. Fully masked sentence-derived titles and unscaffolded short but passage-specific bodies are diagnostic, not automatic failures. Deepening totals are discovered from the frozen corpus, not hardcoded.",
            "title_screen": "Exact within-volume uniqueness, deterministic malformed-title checks, a suffix-matrix screen, and the judge's four-word prefix-family screen (families used at least ten times; fail at 50% affected within a volume). Long sentence-derived titles and non-adjacent rhetorical word repetition are reported diagnostically because the current locked judge read all 65 length-only candidates in context and found them grammatical. All judge-listed title rows are locked to independently reviewed remediated titles and references.",
            "reader_facing_hygiene_screen": "Title, context, body, closing, prayer, response, and journal fields are checked for seven legacy theme labels, stale month/year transition claims, weekday placement, unsupported removal/readiness claims, and Sabbath language detached from either Rest in the Father's Care or a primary verse explicitly naming Sabbath/seventh day.",
            "gospel_parallel_screen": "Every changed Volume 2 primary must preserve original_scripture provenance, be a direct archived OpenBible edge, retain same-verse token overlap and +/-2-verse KJV window token/bigram overlap, honor the five broad-source exclusions and forced Matthew 18:3 -> Mark 10:15 mapping, contain no proven source-only claim attributed to the selected verse, and leave no lexical attribution candidate without a current-hash disposition.",
            "journal_variant_screen": "Prayer-record and follow-through must each contain exactly 12 grammatical question variants across the trilogy and within each volume, with every variant used 30 or 31 times per volume.",
            "judge_remediation_screen": "The independent judge report is hash-locked only as a checklist. Sixteen former title/reference rows must match independently reviewed remediated values; four detached prose phrases must be absent with passage-specific replacements present; and all ten judge-listed grammar rows must contain their repairs with both sentence-level malformed-pattern families at zero.",
            "auditor_neither_screen": "All eight auditor-led Volume 2 remediations are locked to their Scripture references and exact passage-specific replacement sentences. Sentence-leading Neither do or Neither does is prohibited in reader prose fields. scripture_text is excluded from this prose rule and independently KJV-concordance checked; the Mark 11:33 literal is explicitly verified.",
            "interior_screen": "All six DOCX/PDF pairs are checked for package integrity, 6x9 sizing, 395 reader pages and 393 journal pages, blanks, one-to-one title/reference/Scripture mapping, nine journal lines, exact two-line paginated Scripture indexes, and byte identity with the bundle ZIP.",
            "visual_evidence_screen": "The separately authored rendered-page review is hash-locked and must state representative scope, sampled readers/journals, visual defect criteria, and explicit author/KDP/physical-proof exclusions. A valid review satisfies only the local human rendered-page evidence flag.",
            "reproduction_commands": [
                "python3 quality/auditor/run_post_rewrite_manuscript_audit.py",
                "python3 -m json.tool quality/auditor/post-rewrite-manuscript-audit.json >/dev/null",
                "shasum -a 256 downloads/production/revised-reader-edition/volume-1/volume-1-reader-edition.json downloads/production/revised-reader-edition/volume-2/volume-2-reader-edition.json downloads/production/revised-reader-edition/volume-3/volume-3-reader-edition.json",
            ],
            "limitations": [
                "Automated grammar/title screening identifies deterministic defects but does not replace author read-aloud and professional copy editing.",
                "Exact KJV concordance proves identity to the supplied archive, not theological adequacy of application.",
                "Automated DOCX/PDF structure and text checks do not replace a human read-aloud, visual proof, KDP Previewer, or physical-proof review.",
            ],
        },
        "kjv_oracle": kjv_meta,
        "openbible_oracle": openbible_meta,
        "volume_2_gospel_parallel_audit": volume_2_cross_references,
        "volume_results": volume_results,
        "integrity": {
            "count_date_failures": count_date_failures,
            "reference_failures": reference_failures,
            "kjv_text_mismatches": kjv_mismatches,
            "kjv_mismatch_categories": dict(mismatch_categories),
            "reader_markdown_mismatches": reader_mismatches,
            "journal_markdown_mismatches": journal_mismatches,
            "scripture_index_mismatches": index_mismatches,
            "source_provenance_failures": provenance_failures,
            "plural_psalm_references": plural_psalm_references,
        },
        "schema_and_labels": {
            "nonempty_optional_connections": nonempty_optional_connections,
            "rendered_connection_labels": rendered_connection_labels,
            "deprecated_label_hits": deprecated_hits,
        },
        "calendar_internal": {
            "calendar_artifacts": calendar_hits, "internal_language": internal_hits,
            "reader_meta_phrasing": reader_meta_hits,
        },
        "reader_facing_hygiene": reader_hygiene,
        "original_language": {
            "body_leakage": original_language_body,
            "context_contract_failures": context_contract_failures,
        },
        "titles": {
            "exact_duplicates_within_volume": exact_titles_by_volume,
            "exact_duplicates_across_trilogy": cross_volume_titles,
            "near_duplicates_within_volume": near_titles,
            "naturalness_flags": grammar["title_naturalness_flags"],
            "repeated_meaningful_word_flags": meaningful_title_word_repetitions,
            "factory_matrix_audit": title_factory,
        },
        "judge_remediation_audit": judge_remediation,
        "auditor_neither_remediation_audit": neither_remediation,
        "grammar_completeness": grammar,
        "repetition": repetition,
        "removal_claim_audit": removal_claims,
        "deepening_scaffold_audit": deepening_scaffold,
        "severe_generated_template_audit": generated_templates,
        "journal_repetition": journal_repeat,
        "journal_variant_audit": journal_variants,
        "interiors": {
            "build_audit_path": str(INTERIOR_BUILD_AUDIT.relative_to(REPO)),
            "build_audit_sha256": sha256(INTERIOR_BUILD_AUDIT),
            "build_audit_status": build_audit_payload.get("status"),
            "build_audit_mismatches": build_audit_mismatches,
            "artifacts": interior_results,
            "bundle_zip": interior_zip,
        },
        "editorial_score": {
            "score": editorial_score, "minimum": 88, "score_gate_pass": score_gate_pass,
            "method": "Binary weighted binding-gate score; a failed category earns zero points. Passing score does not override any mandatory gate.",
            "gates": gates,
        },
        "manuscript_gate": {
            "verdict": manuscript_verdict,
            "mandatory_gate_failures": [gate["id"] for gate in mandatory_failures],
            "blocking_reasons": manuscript_blocking_reasons,
        },
        "production_artifact_gate": {
            "verdict": artifact_verdict,
            "blocking_reasons": artifact_failures,
        },
        "production_proof_gate": production_proof,
        "release_gate": {
            "verdict": release_verdict,
            "blocking_reasons": release_blocking_reasons,
        },
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({
        "manuscript_verdict": manuscript_verdict,
        "production_artifact_verdict": artifact_verdict,
        "release_verdict": release_verdict, "editorial_score": editorial_score,
        "entries": len(all_entries), "journals": report["scope"]["journal_units"],
        "primary_kjv_mismatches": len(kjv_mismatches),
        "reader_mismatches": len(reader_mismatches), "journal_mismatches": len(journal_mismatches),
        "gospel_reassignments": volume_2_cross_references["reassignments"],
        "gospel_non_edges": len(volume_2_cross_references["non_edges"]),
        "mandatory_gate_failures": report["manuscript_gate"]["mandatory_gate_failures"],
        "artifact_failures": len(artifact_failures),
    }, indent=2))


def render_markdown(report: dict[str, Any]) -> str:
    verdict = report["release_gate"]["verdict"]
    manuscript_verdict = report["manuscript_gate"]["verdict"]
    artifact_verdict = report["production_artifact_gate"]["verdict"]
    score = report["editorial_score"]
    integrity = report["integrity"]
    grammar = report["grammar_completeness"]
    repetition = report["repetition"]
    journal_repeat = report["journal_repetition"]
    journal_variants = report["journal_variant_audit"]
    titles = report["titles"]
    neither = report["auditor_neither_remediation_audit"]
    lines = [
        "# Lady D Trilogy Independent Current-Schema Post-Rewrite Audit",
        "",
        f"**Manuscript gate: {manuscript_verdict}**  ",
        f"**Production-interior artifact gate: {artifact_verdict}**  ",
        f"**Public/KDP release gate: {verdict}**  ",
        f"**Independent editorial score: {score['score']}/100** (binding minimum: {score['minimum']}/100)",
        "",
        "> All earlier and interrupted findings were discarded. This report was recomputed from the final hash-locked one-primary-Scripture corpus only. Empty compatibility fields for an optional second Scripture are not treated as missing content.",
        "",
        "## Hash Lock",
        "",
    ]
    for volume in range(1, 4):
        lines.append(f"- Volume {volume} JSON: `{report['audit_metadata']['verified_json_hashes'][str(volume) if str(volume) in report['audit_metadata']['verified_json_hashes'] else volume]}`")
    lines.extend([
        f"- Contract: `{report['audit_metadata']['contract_path']}`",
        f"- Contract SHA-256: `{report['audit_metadata']['contract_sha256']}`",
        f"- KJV archive SHA-256: `{report['audit_metadata']['verified_source_hashes']['kjv']}`",
        f"- OpenBible archive SHA-256: `{report['audit_metadata']['verified_source_hashes']['openbible']}`",
        f"- Interior ZIP SHA-256: `{report['audit_metadata']['verified_interior_zip_hash']}`",
        f"- Independent judge checklist SHA-256: `{report['audit_metadata']['verified_judge_checklist_hash']}`",
        "",
        "## Executive Finding",
        "",
        f"The current edition contains **{report['scope']['devotional_entries']:,} devotionals**, **{report['scope']['journal_units']:,} matching journal units**, and **{report['scope']['primary_scriptures_checked']:,} required primary KJV quotations**. It contains **{report['scope']['nonempty_optional_second_scriptures']}** nonempty second Scriptures, which is valid under the binding contract.",
        f"The audit also checked **{report['scope']['volume_2_reassignments_checked']}** Volume 2 Gospel reassignments, **{report['scope']['docx_outputs_checked']} DOCX files**, **{report['scope']['pdf_outputs_checked']} PDFs**, and **{report['scope']['pdf_pages_checked']:,} PDF pages**.",
        "",
    ])
    if report["release_gate"]["blocking_reasons"]:
        lines.append("Release remains on hold because:")
        lines.append("")
        for reason in report["release_gate"]["blocking_reasons"]:
            lines.append(f"- **{reason}**")
    else:
        lines.append("Every binding manuscript and production gate passed.")

    lines.extend([
        "", "## Binding Gates", "",
        "| Gate | Weight | Result |",
        "|---|---:|---|",
    ])
    for gate in score["gates"]:
        lines.append(f"| {gate['id']} - {gate['name']} | {gate['weight']} | {'PASS' if gate['pass'] else 'FAIL'} |")

    lines.extend([
        "", "## Corpus Integrity", "",
        "| Check | Result |",
        "|---|---:|",
        f"| Count/date/leap failures | {len(integrity['count_date_failures'])} |",
        f"| Reference/translation failures | {len(integrity['reference_failures'])} |",
        f"| Exact primary KJV mismatches | {len(integrity['kjv_text_mismatches'])} |",
        f"| References using `Psalms` instead of `Psalm` | {len(integrity['plural_psalm_references'])} |",
        f"| Reader JSON/Markdown mismatches | {len(integrity['reader_markdown_mismatches'])} |",
        f"| Journal field/writing-space mismatches | {len(integrity['journal_markdown_mismatches'])} |",
        f"| Scripture Journey Index mismatches | {len(integrity['scripture_index_mismatches'])} |",
        f"| Source-provenance failures | {len(integrity['source_provenance_failures'])} |",
        f"| Rendered second-Scripture labels | {len(report['schema_and_labels']['rendered_connection_labels'])} |",
        f"| Old theme-label hits | {len(report['reader_facing_hygiene']['old_theme_label_hits'])} |",
        f"| Stale month/year transition hits | {len(report['reader_facing_hygiene']['stale_month_year_transition_hits'])} |",
        f"| Detached Sabbath or weekday failures | {len(report['reader_facing_hygiene']['detached_sabbath_failures']) + len(report['reader_facing_hygiene']['weekday_hits'])} |",
        f"| Unsupported removal/readiness claims | {len(report['reader_facing_hygiene']['unsupported_removal_claims']) + len(report['reader_facing_hygiene']['unsupported_readiness_claims'])} |",
        f"| Diagnostic titles with non-adjacent repeated words | {len(titles['repeated_meaningful_word_flags'])} |",
        f"| Sentence-level Scripture-invitation fragments | {len(grammar['scripture_invitation_fragment_failures'])} |",
        f"| Malformed `teach me rest` constructions | {len(grammar['malformed_teach_me_rest_failures'])} |",
        f"| Sentence-leading `Neither do`/`Neither does` reader-prose fragments | {sum(row['reason'] == 'orphaned neither clause' for row in grammar['severe_sentence_fragments'])} |",
        "",
        "## Results by Volume", "",
        "| Vol. | Entries | Body words min/avg/max | Contexts | Monthly reviews | Index rows | Adjacent same-book | Longest run | Failing diversity months |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for key, volume in report["volume_results"].items():
        body = volume["body_words"]
        sequence = volume["sequence"]
        failing_months = len({
            row["month"]
            for row in sequence["months_over_85_percent_one_book"] + sequence["months_under_2_books"]
        })
        lines.append(
            f"| {key} | {volume['entries']} | {body['minimum']}/{body['average']}/{body['maximum']} | "
            f"{volume['context_present']} | {volume['monthly_reviews']} | {volume['index_rows']} | "
            f"{sequence['adjacent_same_book_rate']:.1%} | {sequence['longest_same_book_run']['length']} | {failing_months} |"
        )

    lines.extend(["", "## Exact Current Evidence", ""])
    evidence_sections = [
        ("KJV concordance failures", integrity["kjv_text_mismatches"]),
        ("Plural-Psalms reference failures", integrity["plural_psalm_references"]),
        ("Calendar artifacts", report["calendar_internal"]["calendar_artifacts"]),
        ("Internal production language", report["calendar_internal"]["internal_language"]),
        ("Original-language body leakage", report["original_language"]["body_leakage"]),
        ("Context-contract failures", report["original_language"]["context_contract_failures"]),
        ("Title naturalness flags", titles["naturalness_flags"]),
        ("Diagnostic repeated title-word candidates", titles["repeated_meaningful_word_flags"]),
        ("Missing-verb/title-substitution fragments", grammar["missing_verb_or_title_substitution_fragments"]),
        ("Malformed context fragments", grammar["malformed_context_fragments"]),
        ("Severe sentence fragments", grammar["severe_sentence_fragments"]),
        ("Sentence-level Scripture-invitation fragments", grammar["scripture_invitation_fragment_failures"]),
        ("Malformed teach-me-rest constructions", grammar["malformed_teach_me_rest_failures"]),
        ("Old theme-label hits", report["reader_facing_hygiene"]["old_theme_label_hits"]),
        ("Stale month/year transition hits", report["reader_facing_hygiene"]["stale_month_year_transition_hits"]),
        ("Weekday-placement hits", report["reader_facing_hygiene"]["weekday_hits"]),
        ("Detached Sabbath failures", report["reader_facing_hygiene"]["detached_sabbath_failures"]),
        ("Unsupported removal claims", report["reader_facing_hygiene"]["unsupported_removal_claims"]),
        ("Unsupported readiness claims", report["reader_facing_hygiene"]["unsupported_readiness_claims"]),
    ]
    for heading, rows in evidence_sections:
        lines.append(f"### {heading} ({len(rows)})")
        lines.append("")
        if not rows:
            lines.append("None.")
        else:
            for row in rows[:40]:
                entry_id = row.get("entry_id", "volume-level")
                detail = row.get("excerpts") or row.get("title") or row.get("reference") or row.get("text") or row.get("context") or row.get("matches") or row.get("terms") or row.get("reason") or row
                lines.append(f"- `{entry_id}`: {str(detail)[:500]}")
            if len(rows) > 40:
                lines.append(f"- Full machine-readable list contains {len(rows)} rows.")
        lines.append("")

    exact_within = sum(summary["duplicate_groups"] for summary in titles["exact_duplicates_within_volume"].values())
    lines.extend([
        "## Titles and Repetition", "",
        f"- Exact duplicate-title groups within volumes: **{exact_within}**",
        f"- Exact duplicate-title groups across the trilogy: **{titles['exact_duplicates_across_trilogy']['duplicate_groups']}**",
        f"- Near-title pairs at >=90% within volumes: **{titles['near_duplicates_within_volume']['pair_count']}**",
        f"- Deterministic title-naturalness flags: **{len(titles['naturalness_flags'])}**",
        f"- Judge-reviewed length-only title candidates: **{len(grammar['long_title_review_candidates'])}**",
        f"- Colon titles: **{titles['factory_matrix_audit']['total_colon_titles']}**",
        f"- Volumes with a detected suffix or four-word-prefix title factory: **{len(titles['factory_matrix_audit']['volumes_with_factory_pattern'])}**",
        f"- Exact repeated devotional sentence groups: **{repetition['exact_repeated_sentence_groups']}**",
        f"- Entries affected by exact sentence repetition: **{repetition['exact_repetition_affected_entries']}**",
        f"- Maximum exact sentence reuse: **{repetition['maximum_exact_sentence_reuse']}** entries",
        f"- Masked devotional template groups used in more than three entries: **{repetition['masked_template_groups_over_3']}**",
        f"- Within-entry duplicate sentences: **{repetition['within_entry_duplicate_sentences']}**",
        f"- Substantive journal Reflect/Act groups used in more than three entries: **{journal_repeat['substantive_severe_group_count']}**",
        f"- Repeated journal scaffold groups used in more than thirty entries: **{journal_repeat['scaffold_severe_group_count']}**",
        f"- Severe generated sentence-frame groups over thirty entries: **{len(report['severe_generated_template_audit']['severe_frame_groups'])}**",
        f"- Maximum non-approved generated frame reuse: **{report['severe_generated_template_audit']['maximum_frame_reuse']}** entries",
        "",
    ])
    for volume, result in titles["factory_matrix_audit"]["volumes"].items():
        lines.append(
            f"- Volume {volume} title matrix: **{result['factory_affected_entries']}/{result['entries']}** titles "
            f"({result['factory_affected_share']:.1%}) map to **{result['distinct_assigned_suffix_groups']}** repeated suffix groups."
        )
        for group in result["top_suffix_groups"][:4]:
            sample = "; ".join(example["title"] for example in group["examples"][:2])
            lines.append(f"  - **{group['occurrences']}x** `{group['suffix']}`: {sample}")
        lines.append(
            f"  - Four-word prefix families used >=10x affect **{result['prefix_factory_affected_entries']}/{result['entries']}** titles "
            f"({result['prefix_factory_affected_share']:.1%}) across **{result['distinct_repeated_prefix_groups']}** groups."
        )
        for group in result["top_prefix_groups"][:4]:
            sample = "; ".join(example["title"] for example in group["examples"][:2])
            lines.append(f"    - **{group['occurrences']}x** `{group['prefix']}`: {sample}")
    judge = report["judge_remediation_audit"]
    lines.extend([
        "", "Judge-listed remediation recheck:", "",
        f"- Reviewed title/reference rows: **{judge['reviewed_title_count']}**; failures: **{sum(not row['pass'] for row in judge['reviewed_title_rows'])}**.",
        f"- Detached-prose rows: **{judge['detached_prose_count']}**; failures: **{sum(not row['pass'] for row in judge['detached_prose_rows'])}**.",
        f"- Judge-listed grammar rows: **{judge['grammar_remediation_count']}**; failures: **{sum(not row['pass'] for row in judge['grammar_remediation_rows'])}**.",
        f"- Checklist/source failures: **{len(judge['failures'])}**.",
        f"- Judge prose rows expressed with shorthand rather than fully qualified IDs: **{len(judge['source_list_missing_ids'])}** (diagnostic only; current JSON rows are checked directly).",
    ])
    for row in judge["detached_prose_rows"]:
        lines.append(
            f"  - `{row['entry_id']}`: forbidden phrase absent={'yes' if row['forbidden_phrase_absent'] else 'no'}; "
            f"passage-specific replacement present={'yes' if row['replacement_present'] else 'no'}."
        )
    for row in judge["grammar_remediation_rows"]:
        lines.append(
            f"  - `{row['entry_id']}` ({row['field']}): former defect absent={'yes' if row['forbidden_text_absent'] else 'no'}; "
            f"repair present={'yes' if row['replacement_present'] else 'no'}."
        )
    lines.extend([
        "", "Auditor-led neither-clause remediation recheck:", "",
        f"- Reviewed Volume 2 rows: **{neither['configured_rows']}**; failures: **{len(neither['failures'])}**.",
        f"- Mark 11:33 exact KJV literal verified in `scripture_text`: **{'yes' if neither['mark_11_33_literal_verified'] else 'no'}**.",
        f"- KJV `scripture_text` neither-clause literals excluded from the reader-prose rule: **{len(neither['scripture_text_literals_excluded'])}**.",
    ])
    for row in neither["remediation_rows"]:
        lines.append(
            f"  - `{row['entry_id']}` ({row['scripture_reference']}): former fragment absent={'yes' if row['forbidden_sentence_absent'] else 'no'}; "
            f"passage-specific repair present={'yes' if row['replacement_present'] else 'no'}."
        )
    lines.extend(["", "Claimed production-phrase removals:", ""])
    for key, result in report["removal_claim_audit"]["claims"].items():
        lines.append(
            f"- `{result['phrase']}`: **{result['occurrences']} occurrences** across "
            f"**{result['affected_entries']} entries** ({result['by_volume'] or 'none'})."
        )
    deepening = report["deepening_scaffold_audit"]
    lines.extend(["", "Controlled deepening scaffold (recalculated, not carried forward):", ""])
    for volume, result in deepening["by_volume"].items():
        word_range = (
            "n/a" if result["actual"] == 0
            else f"{result['pre_scaffold_words_minimum']}-{result['pre_scaffold_words_maximum']} words"
        )
        lines.append(
            f"- Volume {volume}: **{result['actual']} detected**; "
            f"pre-scaffold range **{word_range}**."
        )
    lines.extend([
        f"- Trilogy total: **{deepening['actual_total']}**.",
        f"- Threshold violations: **{len(deepening['threshold_violations'])}**.",
        f"- Diagnostic sub-100-word V2/V3 bodies without the scaffold: **{len(deepening['remaining_thin_without_scaffold'])}**.",
        f"- `V2-D187` final remediation: **{'PASS' if deepening['v2_d187_final_remediation']['pass'] else 'FAIL'}** "
        f"({deepening['v2_d187_final_remediation']['whitespace_word_count']} words, "
        f"{deepening['v2_d187_final_remediation']['paragraphs']} paragraphs, "
        f"controlled scaffold={'none' if deepening['v2_d187_final_remediation']['controlled_deepening_opener'] is None else deepening['v2_d187_final_remediation']['controlled_deepening_opener']}).",
    ])
    for row in deepening["threshold_violations"]:
        lines.append(
            f"  - `{row['entry_id']}`: **{row['pre_scaffold_words']} words** before `{row['opener']}` "
            f"(**{row['final_body_words']} words** total); {row['reason']}"
        )
    lines.append("")
    if repetition["all_exact_groups"]:
        lines.append("Most reused devotional sentences:")
        lines.append("")
        for row in repetition["all_exact_groups"][:12]:
            lines.append(f"- **{row['occurrences']}x:** {row['sentence']} (`{', '.join(row['entry_ids'][:6])}`)")
        lines.append("")

    hygiene = report["reader_facing_hygiene"]
    lines.extend([
        "## Reader-Facing Hygiene and Sabbath Placement", "",
        f"- Explicit Sabbath reader entries: **{len(hygiene['explicit_sabbath_entries'])}** ({hygiene['explicit_sabbath_entries_by_volume']}).",
        f"- Justification distribution: **{hygiene['sabbath_justification_counts']}**.",
        f"- Detached Sabbath failures: **{len(hygiene['detached_sabbath_failures'])}**.",
        f"- Weekday hits: **{len(hygiene['weekday_hits'])}**.",
        f"- Old theme-label hits: **{len(hygiene['old_theme_label_hits'])}**.",
        f"- Stale month/year transition hits: **{len(hygiene['stale_month_year_transition_hits'])}**.",
        f"- Unsupported removal/readiness claims: **{len(hygiene['unsupported_removal_claims']) + len(hygiene['unsupported_readiness_claims'])}**.",
        "",
    ])

    lines.extend(["## Primary Scripture Sequencing", ""])
    lines.append("Binding anti-crawl screen: adjacent same-book rate <=35%; no same-book run over seven dated readings; at least two books per month; no month over 85% one book. The JSON also retains stricter 40%/four-book diversity diagnostics without treating them as binding.")
    lines.append("")
    for key, volume in report["volume_results"].items():
        sequence = volume["sequence"]
        lines.append(
            f"- Volume {key}: {sequence['adjacent_same_book_rate']:.1%} adjacent same-book; longest run "
            f"{sequence['longest_same_book_run']['length']} ({sequence['longest_same_book_run']['book']}); "
            f"{len(sequence['months_over_85_percent_one_book'])} months over 85%; "
            f"{len(sequence['months_under_2_books'])} months under two books."
        )

    cross = report["volume_2_gospel_parallel_audit"]
    lines.extend([
        "", "## Volume 2 Gospel Parallel Audit", "",
        f"- Reassigned rows checked: **{cross['reassignments']}** (expected {cross['expected_reassignments']})",
        f"- Direct OpenBible edges: **{cross['direct_edge_count']}**",
        f"- Non-edges: **{len(cross['non_edges'])}**",
        f"- Verse/window overlap failures: **{len(cross['overlap_failures'])}**",
        f"- Broad-exclusion failures: **{len(cross['broad_exclusion_failures'])}**",
        f"- Forced-mapping failures: **{len(cross['forced_mapping_failures'])}**",
        f"- Confirmed source/primary attribution mismatches: **{len(cross['proven_semantic_source_mismatches'])}**",
        f"- Lexical attribution candidates reviewed: **{len(cross['semantic_review_candidates'])}**",
        f"- Reviewed immediate-context nonfailures: **{len(cross['reviewed_contextual_nonfailures'])}**",
        f"- Unreviewed semantic candidates: **{len(cross['unreviewed_semantic_candidates'])}**",
        f"- Edge votes min/median/max: **{cross['vote_summary']['minimum']}/{cross['vote_summary']['median']}/{cross['vote_summary']['maximum']}**",
        f"- Minimum verse-token / window-token / window-bigram overlap: **{cross['overlap_summary']['minimum_verse_token_overlap']}/{cross['overlap_summary']['minimum_window_token_overlap']}/{cross['overlap_summary']['minimum_window_bigram_overlap']}**",
        f"- Target-book distribution: **{cross['target_book_counts']}**",
        "",
    ])
    if cross["non_edges"]:
        lines.append("Non-edge rows:")
        lines.append("")
        for row in cross["non_edges"][:30]:
            lines.append(f"- `{row['entry_id']}`: {row['original']} -> {row['current']}")
        lines.append("")
    if cross["proven_semantic_source_mismatches"]:
        lines.append("Proven source/primary mismatches:")
        lines.append("")
        for row in cross["proven_semantic_source_mismatches"][:30]:
            evidence = row.get("quoted_text") or row.get("claim") or "See machine-readable evidence."
            lines.append(f"- `{row['entry_id']}`: {row['reason']} Evidence: {evidence}")
        lines.append("")
    if cross["reviewed_contextual_nonfailures"]:
        lines.append("Reviewed immediate-context nonfailures:")
        lines.append("")
        for row in cross["reviewed_contextual_nonfailures"]:
            lines.append(
                f"- `{row['entry_id']}` ({row['original']} -> {row['current']}): "
                f"{row['reason']} Claim reviewed: {row['claim']}"
            )
        lines.append("")

    lines.extend([
        "", "## Journal Contract", "",
        f"- Journal render/field/spacing mismatches: **{len(integrity['journal_markdown_mismatches'])}**",
        "- Expected writing space: nine underscore lines per unit.",
        "- Expected monthly rhythm: one review after each of twelve months.",
        f"- Repeated substantive prompt groups over three entries: **{journal_repeat['substantive_severe_group_count']}**",
        f"- Prayer-record variants: **{journal_variants['fields']['journal_prayer_record']['unique_variants']}/12**",
        f"- Follow-through variants: **{journal_variants['fields']['journal_follow_through']['unique_variants']}/12**",
        f"- Variant grammar/distribution failures: **{len(journal_variants['failures'])}**",
        "",
        "## Interior Artifact Audit", "",
        f"**Production-interior artifact gate: {artifact_verdict}**",
        "",
    ])
    if report["production_artifact_gate"]["blocking_reasons"]:
        for reason in report["production_artifact_gate"]["blocking_reasons"]:
            lines.append(f"- {reason}")
    else:
        lines.append("- All DOCX, PDF, build-audit, index, and ZIP checks passed.")
    lines.append("")
    lines.extend([
        "| Vol. | Reader PDF | Journal PDF | DOCX sync | Reader index rows | Reader index titles | Biblical order |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for key, artifacts in report["interiors"]["artifacts"].items():
        reader_pdf = artifacts["reader"]["pdf"]
        journal_pdf = artifacts["journal"]["pdf"]
        docx_mismatches = len(artifacts["reader"]["docx"]["mismatches"]) + len(artifacts["journal"]["docx"]["mismatches"])
        index = reader_pdf["scripture_index"] or {}
        lines.append(
            f"| {key} | {reader_pdf['pages']} pages | {journal_pdf['pages']} pages | "
            f"{docx_mismatches} mismatches | {index.get('rows_verified', 0)}/366 | "
            f"{index.get('titles_present', 0)}/366 | {'PASS' if index.get('biblical_order_pass') else 'FAIL'} |"
        )
    for key, artifacts in report["interiors"]["artifacts"].items():
        index = artifacts["reader"]["pdf"]["scripture_index"] or {}
        for inversion in index.get("order_inversions", []):
            lines.append(
                f"- Volume {key} order inversion: `{inversion['previous_reference']}` appears before "
                f"`{inversion['current_reference']}`."
            )
    lines.extend([
        "",
        "## Production-Proof Boundary", "",
        f"**{report['production_proof_gate']['status']}**",
        "",
        report["production_proof_gate"]["note"],
        "",
        f"- Local rendered-page evidence: {'PASS' if report['production_proof_gate']['human_rendered_page_visual_approval_evidenced'] else 'NOT EVIDENCED'}",
        f"- Final author visual approval: {'EVIDENCED' if report['production_proof_gate']['final_author_visual_approval_evidenced'] else 'NOT EVIDENCED'}",
        f"- KDP Previewer: {'EVIDENCED' if report['production_proof_gate']['kdp_previewer_evidenced'] else 'NOT EVIDENCED'}",
        f"- Physical proof: {'EVIDENCED' if report['production_proof_gate']['physical_proof_approval_evidenced'] else 'NOT EVIDENCED'}",
        f"- Visual-review evidence: `{report['production_proof_gate']['local_rendered_page_visual_evidence']['path']}` (`{report['production_proof_gate']['local_rendered_page_visual_evidence']['verified_sha256']}`)",
        "",
        "## Reproduction", "", "```bash",
    ])
    lines.extend(report["methodology"]["reproduction_commands"])
    lines.extend([
        "```", "",
        "The script writes only this Markdown report and its JSON companion. It does not modify devotional or journal manuscripts.",
        "", "## Required Disposition", "",
        f"**Public/KDP release: {verdict}.** Manuscript and production-artifact verdicts remain separate above. "
        f"{'A current representative local rendered-page review is recorded' if report['production_proof_gate']['human_rendered_page_visual_approval_evidenced'] else 'The available local rendered-page review predates the current frozen artifacts'}; "
        f"public release remains prohibited until final author visual approval, KDP Previewer approval, and physical-proof approval are evidenced.", "",
    ])
    return "\n".join(lines)


if __name__ == "__main__":
    main()
