#!/usr/bin/env python3
"""Build the transcript-directed Lady D trilogy reader edition.

This builder preserves the complete historical production masters, then creates
new reader-facing manuscripts with visible KJV text, a thematic scripture
journey, cleaner daily endings, revised titles, companion journals, and a
machine-auditable release contract.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
import zipfile
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "downloads" / "production" / "master"
OUT = ROOT / "downloads" / "production" / "revised-reader-edition"
PUBLIC_OUT = ROOT / "public" / "downloads" / "production" / "revised-reader-edition"
KJV_ZIP = ROOT / "source" / "scripture" / "eng-kjv2006_usfm.zip"
CROSS_REFERENCES_ZIP = ROOT / "source" / "scripture" / "openbible-cross-references.zip"
GENERATED = date(2026, 7, 19).isoformat()
AUTHOR = 'Susan "Lady D" Damon'
ENABLE_AUTOMATIC_CONNECTIONS = False


MONTHS = [
    ("January", 31),
    ("February", 28),
    ("March", 31),
    ("April", 30),
    ("May", 31),
    ("June", 30),
    ("July", 31),
    ("August", 31),
    ("September", 30),
    ("October", 31),
    ("November", 30),
    ("December", 31),
]

BOOK_CODES = {
    "GEN": "Genesis",
    "EXO": "Exodus",
    "LEV": "Leviticus",
    "NUM": "Numbers",
    "DEU": "Deuteronomy",
    "JOS": "Joshua",
    "JDG": "Judges",
    "RUT": "Ruth",
    "1SA": "1 Samuel",
    "2SA": "2 Samuel",
    "1KI": "1 Kings",
    "2KI": "2 Kings",
    "1CH": "1 Chronicles",
    "2CH": "2 Chronicles",
    "EZR": "Ezra",
    "NEH": "Nehemiah",
    "EST": "Esther",
    "JOB": "Job",
    "PSA": "Psalm",
    "PRO": "Proverbs",
    "ECC": "Ecclesiastes",
    "SNG": "Song of Solomon",
    "ISA": "Isaiah",
    "JER": "Jeremiah",
    "LAM": "Lamentations",
    "EZK": "Ezekiel",
    "DAN": "Daniel",
    "HOS": "Hosea",
    "JOL": "Joel",
    "AMO": "Amos",
    "OBA": "Obadiah",
    "JON": "Jonah",
    "MIC": "Micah",
    "NAM": "Nahum",
    "HAB": "Habakkuk",
    "ZEP": "Zephaniah",
    "HAG": "Haggai",
    "ZEC": "Zechariah",
    "MAL": "Malachi",
    "MAT": "Matthew",
    "MRK": "Mark",
    "LUK": "Luke",
    "JHN": "John",
    "ACT": "Acts",
    "ROM": "Romans",
    "1CO": "1 Corinthians",
    "2CO": "2 Corinthians",
    "GAL": "Galatians",
    "EPH": "Ephesians",
    "PHP": "Philippians",
    "COL": "Colossians",
    "1TH": "1 Thessalonians",
    "2TH": "2 Thessalonians",
    "1TI": "1 Timothy",
    "2TI": "2 Timothy",
    "TIT": "Titus",
    "PHM": "Philemon",
    "HEB": "Hebrews",
    "JAS": "James",
    "1PE": "1 Peter",
    "2PE": "2 Peter",
    "1JN": "1 John",
    "2JN": "2 John",
    "3JN": "3 John",
    "JUD": "Jude",
    "REV": "Revelation",
}
BOOK_ORDER = {name: index for index, name in enumerate(BOOK_CODES.values(), start=1)}


@dataclass(frozen=True)
class Theme:
    name: str
    promise: str
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class Book:
    volume: int
    title: str
    subtitle: str
    lane: str
    accent: str
    cover: str
    themes: tuple[Theme, ...]


@dataclass
class Entry:
    original_day: float
    original_date: str
    original_title: str
    scripture: str
    lens: str
    body: list[str]
    step: str
    prayer: str
    prompt: str
    impact: str
    source_heading: str
    source_scripture: str = ""
    book: str = ""
    chapter: int = 0
    verse: int = 0
    scripture_text: str = ""
    core: str = ""
    assigned_theme: int = 0
    day_number: int = 0
    date_label: str = ""
    title: str = ""
    context_label: str = "Scripture context"
    closing: str = ""
    connection_reference: str = ""
    connection_text: str = ""
    connection_book: str = ""


def t(name: str, promise: str, *keywords: str) -> Theme:
    return Theme(name, promise, tuple(keywords))


BOOKS = (
    Book(
        1,
        "Surrendering to God's Love",
        "A 365-Day Devotional Journey into the Father's Heart",
        "God the Father",
        "#8f5d2f",
        "production-assets/author-review-covers/volume-1-author-review-cover.png",
        (
            t("Loved Before You Perform", "Receive belonging before the day asks anything from you.", "love", "beloved", "welcome", "chosen", "identity", "receive", "performance"),
            t("Trusting the Father's Heart", "Let covenant faithfulness become steadier than changing feelings.", "trust", "faithful", "promise", "covenant", "cling", "father"),
            t("Grace for the Hidden Places", "Bring shame, fear, and guarded places into honest grace.", "grace", "shame", "fear", "hide", "hidden", "heart", "honest"),
            t("Mercy That Restores", "Receive mercy that tells the truth and still rebuilds.", "mercy", "forgive", "forgiveness", "compassion", "restore", "healing"),
            t("Surrendering Control", "Trade anxious control for the next faithful yes.", "surrender", "control", "yield", "obey", "obedience", "choose"),
            t("Provision and Presence", "Notice the Father who is near in ordinary need.", "provide", "need", "bread", "home", "presence", "near", "carry"),
            t("Rest in the Father's Care", "Receive holy rest as a gift of trust and belonging.", "rest", "sabbath", "peace", "quiet", "weary", "burden"),
            t("Courage to Be Known", "Let God's naming become stronger than fear's labels.", "courage", "truth", "identity", "name", "known", "seen"),
            t("Love That Changes How We Live", "Turn received love into practical mercy, justice, and welcome.", "service", "neighbor", "justice", "mercy", "welcome", "kindness"),
            t("Hope While You Wait", "Trust the Father's work when the timeline is still unfinished.", "hope", "wait", "patience", "delay", "promise", "future"),
            t("Held Through the Storm", "Discover steadfast love in grief, trouble, and uncertainty.", "grief", "sorrow", "storm", "trouble", "refuge", "tears"),
            t("Love Made Visible", "Let gratitude and generosity reveal the Father in the final movement.", "gratitude", "joy", "praise", "blessing", "give", "worship"),
        ),
    ),
    Book(
        2,
        "Walking with Jesus",
        "A 365-Day Devotional Journey with the Son",
        "Jesus the Son",
        "#356f73",
        "production-assets/author-review-covers/volume-2-author-review-cover.png",
        (
            t("The Invitation to Follow", "Move from admiring Jesus to walking with Him.", "follow", "call", "invite", "disciple", "road"),
            t("Learning His Voice", "Let the words of Jesus become louder than approval and fear.", "listen", "voice", "word", "truth", "teacher"),
            t("The Way of the Kingdom", "Receive the surprising values of the King in ordinary life.", "kingdom", "way", "truth", "command", "teach"),
            t("Mercy at the Table", "Meet the Jesus who welcomes, feeds, and restores people.", "table", "mercy", "compassion", "welcome", "feed"),
            t("Faith That Reaches for Jesus", "Bring real need to the One who heals and makes whole.", "heal", "faith", "touch", "mercy", "blind", "whole"),
            t("Prayer and Abiding", "Stay near enough for prayer to become relationship.", "pray", "prayer", "abide", "near", "remain"),
            t("The Cross-Shaped Life", "Let surrender make room for resurrection life.", "cross", "deny", "surrender", "sacrifice", "life"),
            t("Serving in His Steps", "Practice the humility of Jesus in hidden and public service.", "serve", "servant", "humble", "wash", "least"),
            t("Courage to Witness", "Carry the truth of Jesus with courage and gentleness.", "witness", "speak", "courage", "send", "testimony"),
            t("Life Together in Christ", "Let forgiveness and peace shape the people around the table.", "forgive", "community", "brother", "peace", "together"),
            t("Following Through the Hard Road", "Stay with Jesus when obedience is costly and slow.", "endure", "trial", "suffer", "wait", "faithful"),
            t("Resurrection Hope", "Walk into the future with the risen Christ.", "resurrection", "hope", "rise", "glory", "return", "life"),
        ),
    ),
    Book(
        3,
        "Filled with the Holy Spirit",
        "A 365-Day Devotional Journey of Presence, Power, and Fruit",
        "The Holy Spirit",
        "#7a4b75",
        "production-assets/author-review-covers/volume-3-author-review-cover.png",
        (
            t("The Promise of His Presence", "Begin with the Spirit as God's near and faithful gift.", "promise", "presence", "comfort", "near", "spirit"),
            t("Open Hands, Filled Life", "Yield the rooms of life that self-effort cannot fill.", "fill", "filled", "yield", "surrender", "receive"),
            t("Fruit That Can Be Seen", "Let the Spirit form character deeper than appearance.", "fruit", "love", "joy", "peace", "patience", "gentle"),
            t("Led by the Spirit", "Learn the difference between pressure and holy guidance.", "lead", "led", "guide", "truth", "voice", "wisdom"),
            t("Prayer in the Deep Places", "Welcome the Helper into burdens too deep for polished words.", "pray", "prayer", "intercede", "groan", "burden"),
            t("Gifts for Faithful Work", "Receive spiritual gifts as tools for service, not display.", "gift", "work", "wisdom", "skill", "serve"),
            t("Power to Witness", "Let holy power make Jesus visible through courage and love.", "power", "witness", "bold", "send", "testimony"),
            t("Freedom and Healing", "Invite the Spirit into bondage, wounds, and weary places.", "free", "freedom", "heal", "deliver", "bond", "dry"),
            t("One Body, One Spirit", "Practice unity without erasing truth or difference.", "unity", "body", "together", "church", "peace"),
            t("Holy Fire", "Let conviction refine motives without turning grace into shame.", "fire", "holy", "refine", "convict", "purify"),
            t("Comfort for the Long Night", "Receive the Comforter in grief, waiting, and endurance.", "comfort", "grief", "night", "wait", "endure", "tears"),
            t("Renewed for What Comes Next", "Receive fresh oil, living hope, and surrendered expectancy for what comes next.", "renew", "hope", "rain", "oil", "new", "future"),
        ),
    ),
)


DEEPENING_COUNSEL = {
    2: (
        "following Jesus becomes real when trust loosens its grip on control and takes the next obedient step while the outcome is still unseen",
        "the voice of Jesus must be heard long enough to challenge approval, fear, and the private scripts that have been setting the pace",
        "kingdom life overturns the instinct to protect status and teaches the heart to choose truth, mercy, and obedience in ordinary decisions",
        "mercy at the table makes room for real people without pretending that wounds, hunger, failure, or the need for repentance are imaginary",
        "faith reaches for Jesus with an honest need and stays open to the way His healing may restore more than the symptom first named",
        "prayer becomes relationship when the heart stops presenting a polished report and remains with Jesus long enough to listen and answer honestly",
        "the cross-shaped life releases the demand to preserve comfort at every cost and receives resurrection life through surrendered obedience",
        "serving in the steps of Jesus means choosing hidden faithfulness over recognition and treating the person in front of us as worthy of patient love",
        "courageous witness tells the truth about Jesus with gentleness, refuses performance, and leaves the result in the hands of the One who sends",
        "life together in Christ requires forgiveness with boundaries, peace with truth, and the humility to let love reshape the atmosphere around us",
        "the hard road tests whether closeness to Jesus matters more than quick relief, public understanding, or the appearance of effortless faith",
        "resurrection hope gives the future back to Christ and teaches the heart to act from promised life instead of rehearsing the power of the grave",
    ),
    3: (
        "the promise of the Spirit meets actual weakness with God's presence, not with pressure to manufacture a spiritual feeling or impressive result",
        "an open-handed life lets the Spirit enter rooms self-effort has managed, hidden, defended, or tried to fill with control",
        "visible fruit grows through repeated surrender, especially where patience, gentleness, courage, and self-control cost more than appearance",
        "holy guidance becomes clearer when urgency quiets down and the heart tests its impulses against Scripture, the character of Jesus, and wise counsel",
        "prayer in deep places gives grief, weariness, confusion, and wordless need permission to come before God without religious performance",
        "spiritual gifts become trustworthy when they serve the body, honor Jesus, welcome accountability, and refuse to turn usefulness into identity",
        "power to witness is not volume or display; it is courage under surrender, truth carried with love, and a life that makes Jesus visible",
        "freedom and healing invite the Spirit into the wound without denying its history and into the habit without surrendering hope for change",
        "one body and one Spirit call believers to unity that can tell the truth, honor difference, repair harm, and stay at the table",
        "holy fire exposes what love intends to heal, so conviction can lead to confession and freedom instead of shame, hiding, or spectacle",
        "the Comforter stays near in the long night, holding grief without rushing it and strengthening hope when answers remain unfinished",
        "renewal for what comes next begins with fresh surrender, living hope, and a willingness to receive the Spirit's next faithful instruction",
    ),
}


SAFE_TITLE_PATTERNS = (
    "{theme}: A Quiet Beginning",
    "{theme}: Meeting the Morning",
    "{theme}: The Courage to Receive",
    "{theme}: Grace for the Hidden Place",
    "{theme}: Learning to Live the Word",
    "{theme}: Where Grace Takes Root",
    "{theme}: A Faithful Yes",
    "{theme}: The Next Step",
    "{theme}: Grace to Practice",
    "{theme}: Making Room for God",
    "{theme}: Faith in the Ordinary Place",
    "{theme}: What the Heart Must Answer",
    "{theme}: A Steady Walk",
    "{theme}: The Gift Within",
    "{theme}: When the Road Is Hard",
    "{theme}: Returning to God",
    "{theme}: The Freedom to Respond",
    "{theme}: Holding Fast",
    "{theme}: The Next Conversation",
    "{theme}: A Life Being Shaped",
    "{theme}: The Honest Work",
    "{theme}: Faith Without Performance",
    "{theme}: Trusting God Again",
    "{theme}: The Strength to Choose",
    "{theme}: Standing at the Threshold",
    "{theme}: Peace for the Present",
    "{theme}: Carrying Grace into the Day",
    "{theme}: Hope for What Comes Next",
    "{theme}: A Deeper Surrender",
    "{theme}: Fruit That Can Be Seen",
    "{theme}: Finishing with Faith",
    "{theme}: A Place for Honest Prayer",
    "{theme}: Mercy for the Next Step",
    "{theme}: Truth for the Waiting Heart",
    "{theme}: Courage in the Unfinished Place",
    "{theme}: The Way Forward",
    "{theme}: Hope Under Pressure",
    "{theme}: A Heart Open to God",
    "{theme}: Strength for One More Step",
    "{theme}: The Grace to Begin Again",
    "{theme}: Faithfulness in Small Things",
)

NATURAL_TITLE_SUFFIXES = (
    "at Morning's First Light",
    "in the Ordinary Day",
    "When the Road Is Hard",
    "with Open Hands",
    "for the Next Faithful Step",
    "in Quiet Trust",
    "Where Courage Begins",
    "for the Waiting Heart",
    "When Answers Are Slow",
    "in the Hidden Place",
    "with an Honest Heart",
    "for the Work Ahead",
    "When Fear Speaks",
    "in Family Life",
    "for One More Step",
    "When Mercy Costs Something",
    "in the Unfinished Place",
    "Where Hope Takes Root",
    "in the Long Night",
    "for the Next Conversation",
    "Where Grace Meets Pressure",
    "When the Heart Is Tired",
    "in Small Faithfulness",
    "for a New Beginning",
    "Where Love Becomes Visible",
    "When Control Feels Safer",
    "in the Place of Need",
    "for the Person in Front of You",
    "When Waiting Stretches",
    "Where Truth Meets Tenderness",
    "for the Road Ahead",
    "before the Day Begins",
    "after the Noise Fades",
    "at the Open Door",
    "beside Still Waters",
    "under Open Skies",
    "with Room to Breathe",
    "as the Heart Softens",
    "beyond the Need to Prove",
    "while the Door Is Open",
    "where the Wound Still Aches",
    "for the Choice in Front of You",
    "when the Old Fear Returns",
    "in the Room No One Sees",
    "with the Truth You Already Know",
    "before Another Step Is Taken",
    "where Grace Has Cleared a Path",
    "when the Soul Needs Rest",
    "in the Middle of Change",
    "with Courage for Today",
    "where Surrender Becomes Freedom",
    "when the Answer Requires Patience",
    "in the Work of Becoming",
    "with Mercy for Yourself",
    "where the Next Yes Matters",
    "when the Heart Wants to Hide",
    "in the Practice of Peace",
    "with Hope for the Unfinished Story",
    "where Faith Meets Real Life",
    "when Love Must Become Action",
    "in the Presence of God",
    "with Strength for the Honest Choice",
    "where the Light Finds You",
    "when the Way Forward Is Narrow",
    "in the Care of the Father",
    "with Jesus in the Storm",
    "where the Spirit Gives Breath",
    "when Prayer Has No Easy Words",
    "in the Quiet After the Question",
    "with Grace for the Next Hour",
    "where Obedience Begins Small",
    "when the Heart Learns to Listen",
    "in the Space Between Answers",
    "with Peace That Does Not Perform",
    "where Mercy Rewrites the Ending",
    "when Trust Must Outlast Feeling",
    "in the Hands of Faithful Love",
    "with a Clearer Yes",
    "where the Burden Can Be Named",
    "when the Road Turns Unexpectedly",
    "in the Shelter of His Presence",
    "with Truth for the Tender Place",
    "where Hope Refuses to Leave",
    "when Grace Interrupts the Pattern",
    "in the Freedom of Being Known",
    "with Patience for Slow Growth",
    "where Love Outlives the Fear",
    "when Faith Enters the Conversation",
    "in the Courage of Quiet Obedience",
    "with Compassion for the Wounded Place",
    "where God Meets the Real Need",
    "when the Heart Chooses to Stay",
    "in the Light of a New Mercy",
    "with Open Hands for What Comes",
    "where the Promise Holds Firm",
    "when the Next Step Costs Something",
)

TITLE_SUBJECTS = {
    1: (
        "The Father's Welcome", "Love Has the First Word", "Mercy Meets You",
        "Grace Holds the Door Open", "Already Beloved", "The Love That Stays",
        "Held by the Father", "Trust Begins Here", "Grace Before Striving",
        "The Father's Steady Hand", "Belonging Before Performance", "Hope Under His Care",
        "Rest for the Proving Heart", "Known and Still Loved", "Surrender Without Fear",
        "The Courage to Be Held", "Love That Changes Us", "The Father's Faithful Presence",
        "Welcome Before the Work", "Love Stronger Than Shame", "The Father Sees You",
        "Mercy for the Weary", "Grace in the Real Story", "Safe in His Keeping",
        "Loved Before You Answer", "The Father Has Not Left", "His Care Is Already Here",
        "A Home for the Honest Heart", "Held Through the Waiting", "The God Who Comes Near",
        "Love Without a Scorecard", "Grace for the Wounded Place", "Trusting the Father's Heart",
        "His Mercy Makes Room", "The Father Knows the Cost", "Love That Tells the Truth",
    ),
    2: (
        "Jesus Calls You Closer", "The Road with Jesus", "His Voice Sets the Pace",
        "Grace Beside the Road", "The Next Faithful Step", "At the Table with Jesus",
        "Learning the Way of Christ", "Near Enough to Be Changed", "Mercy in His Footsteps",
        "A Courage Shaped Like Christ", "The Friend Who Leads", "Walking Truth in Love",
        "The Cross Before Comfort", "Following When It Costs", "Prayer That Stays Near",
        "The Kingdom in Ordinary Life", "Resurrection Changes the Road", "Jesus Is Already There",
        "Jesus Meets You Here", "The Shepherd Knows the Road", "Christ at the Center",
        "Mercy with Skin On", "The Savior Who Notices", "Learning to Stay Near",
        "His Presence Changes the Room", "Jesus Holds the Question", "The King Who Serves",
        "Grace in His Gaze", "Following the Gentle King", "Christ Makes a Way",
        "The Teacher at Your Side", "A Table Wide Enough", "Jesus Speaks into Fear",
        "His Mercy Goes First", "The Risen Christ Is Near", "Walking at His Pace",
    ),
    3: (
        "The Spirit Is Near", "Open Hands for Holy Power", "The Comforter Stays",
        "Where the Wind Leads", "Fruit Before Display", "The Presence You Cannot Manufacture",
        "Holy Fire and Tender Hearts", "Wisdom for the Work Ahead", "Prayer Beyond Words",
        "Freedom in the Spirit", "Power Under Surrender", "The Breath of God",
        "Fresh Oil for the Journey", "Gifts That Serve in Love", "One Body, One Spirit",
        "Comfort for the Long Night", "Renewal Begins with Surrender", "Filled for Faithful Work",
        "The Spirit Breathes Again", "Strength That Stays Tender", "The Spirit Meets the Need",
        "Power with a Servant's Heart", "The Comforter Draws Near", "Holy Presence in Ordinary Life",
        "The Spirit Opens the Way", "Grace for the Inner Work", "The Spirit Forms What Lasts",
        "Fire That Purifies Gently", "Breath for the Weary Place", "The Spirit Teaches the Heart",
        "Power That Does Not Perform", "The Gift of Holy Presence", "The Spirit Strengthens Surrender",
        "Fruit Born in Secret", "The Comforter Holds the Night", "Guidance for the Faithful Step",
    ),
}

TITLE_OVERRIDES = {
    (1, "Genesis 15:2"): "Questions That Belong Inside the Promise",
    (1, "Exodus 20:6"): "Love with a Holy Shape",
    (1, "Genesis 32:32"): "Remembering the Mercy That Changed Your Walk",
    (1, "Genesis 1:11"): "A Seed Can Carry the Promise",
    (1, "Genesis 50:2"): "Love Tends What Remains",
    (1, "Genesis 1:21"): "Life Called Good Before Striving",
    (2, "Mark 6:49"): "When Fear Misreads Help",
    (2, "Mark 3:18"): "Receiving the People Jesus Calls Near",
    (2, "Mark 2:25"): "Mercy Is How Jesus Reads the Need",
    (2, "Luke 12:6"): "Nothing Small Is Overlooked by the Father",
    (2, "Mark 8:15"): "The Hidden Influence Shaping Your Heart",
    (2, "Mark 11:31"): "The Honest Answer Obedience Requires",
    (2, "Matthew 20:33"): "A Plain Prayer for Open Eyes",
    (2, "Mark 10:28"): "An Honest Question About the Cost of Following",
    (2, "Mark 13:11"): "Peace Before the Pressured Conversation",
    (2, "Luke 12:4"): "When Reverence Becomes Stronger Than Fear",
    (2, "Matthew 12:20"): "Gentleness for What Is Bruised and Barely Burning",
    (2, "Luke 9:41"): "Correction That Does Not Cancel Mercy",
    (2, "Matthew 25:31"): "The King Who Sets All Things Right",
    (2, "Mark 10:15"): "Receiving the Kingdom with a Childlike Heart",
    (3, "Exodus 35:9"): "What Is Precious Can Be Prepared for Holy Use",
    (3, "Judges 14:20"): "Bringing Relational Grief into God's Presence",
    (3, "Judges 6:5"): "Pressure Is Not the Same as God's Absence",
    (3, "Judges 6:29"): "Courage While the Questions Are Still Spreading",
    (3, "Numbers 11:28"): "When Another Person's Gift Feels Threatening",
    (3, "1 Samuel 10:25"): "Calling Needs Order",
    (3, "Matthew 10:40"): "Welcome That Carries the Presence of Jesus",
    (3, "Judges 3:5"): "The Influence of the Room Around You",
    (3, "Matthew 10:13"): "Offer Peace and Release the Outcome",
    (3, "Matthew 10:39"): "The Life Surrendered Is the Life Truly Found",
    (3, "Judges 15:15"): "When a Tool Starts Feeling Like Your Identity",
    (3, "Matthew 10:17"): "Opposition Does Not Get the Final Name",
    (3, "Matthew 10:25"): "Faithful Love Can Be Called by the Wrong Name",
    (3, "Numbers 27:12"): "Blessing What You Cannot Control or Complete",
    (3, "Matthew 10:32"): "When Confession Becomes Obedience",
    (3, "Genesis 2:15"): "Placed in the Garden for Faithful Work",
    (3, "Judges 6:39"): "Mercy for a Heart That Needs Assurance",
    (3, "Judges 3:7"): "Remembering Whom Your Heart Belongs To",
    (3, "Judges 15:10"): "Truthful Witness Under Pressure",
    (3, "Numbers 27:17"): "A Shepherd for the People Ahead",
    (3, "Genesis 1:29"): "Provision Before Striving",
    (3, "Judges 6:20"): "Obedience Before Display",
    (3, "Judges 6:22"): "Holy Awe After the Encounter",
}

PASSAGE_BODY_REWRITES = {
    (2, "Matthew 15:11"): (
        "Neither do your worst words, your reactive moment, or the pressure that exposed you.",
        (
            "Your worst words, your reactive moment, and the pressure that exposed you do not "
            "have the final word over the heart Jesus wants to heal."
        ),
    ),
    (2, "Mark 6:3"): (
        "Neither do other people's small labels.",
        "Other people's small labels do not define what Jesus is forming in you.",
    ),
    (2, "Matthew 13:41"): (
        "Neither does the sin you are surrendering.",
        "The sin you are surrendering does not have the final word over your life.",
    ),
    (2, "Matthew 17:13"): (
        "Neither does yesterday's confusion.",
        "Yesterday's confusion does not disqualify today's understanding.",
    ),
    (2, "Mark 8:5"): (
        "Neither does scarcity, comparison, or the fear that your little is too little.",
        (
            "Scarcity, comparison, and the fear that your little is too little do not limit "
            "what Jesus can do with surrendered provision."
        ),
    ),
    (2, "Mark 8:35"): (
        "Neither does the sacrifice, the loss, or the obedience you are afraid will cost too much.",
        (
            "The sacrifice, loss, or obedience you fear will cost too much does not outweigh "
            "the life Jesus gives."
        ),
    ),
    (2, "Matthew 15:21"): (
        "Neither does the region, the transition, the unanswered question, or the place where you feel out of your depth.",
        (
            "The region, the transition, the unanswered question, and the place where you feel "
            "out of your depth do not remove you from His leadership."
        ),
    ),
    (2, "Mark 6:17"): (
        "Neither does the prison, the accusation, the delay, or the hard backstory.",
        (
            "The prison, the accusation, the delay, and the hard backstory do not place the "
            "story beyond Jesus' presence."
        ),
    ),
    (2, "Mark 6:49"): (
        (
            "kingdom life overturns the instinct to protect status and teaches the heart "
            "to choose truth, mercy, and obedience in ordinary decisions"
        ),
        (
            "fear loses authority when the heart lets Jesus name His nearness and receives "
            "His word before reacting"
        ),
    ),
    (3, "Judges 14:20"): (
        (
            "spiritual gifts become trustworthy when they serve the body, honor Jesus, "
            "welcome accountability, and refuse to turn usefulness into identity"
        ),
        (
            "grief must be brought into God's presence before betrayal is allowed to harden "
            "the heart or direct the next choice"
        ),
    ),
    (3, "Judges 6:29"): (
        (
            "one body and one Spirit call believers to unity that can tell the truth, honor "
            "difference, repair harm, and stay at the table"
        ),
        (
            "settled courage can tell the truth, withstand accusation, and wait for God "
            "without turning every question into a fight"
        ),
    ),
}

INVITATION_TRANSITIONS = (
    "Put the passage into practice by",
    "Respond to the Scripture by",
    "Carry the truth into the day by",
    "Let the passage become lived obedience by",
    "Answer this word by",
    "Take the next faithful step by",
    "Receive the passage's invitation by",
    "Bring the Scripture into ordinary life by",
    "Move from reflection to response by",
    "Let the reading shape one choice by",
    "Follow the Scripture's direction by",
    "Practice what the verse reveals by",
    "Make room for this truth by",
    "Live the passage with honesty by",
    "Turn insight into faithfulness by",
    "Let the Word take root by",
)

SABBATH_TRANSITIONS = (
    "During Sabbath rest, remember:",
    "Sabbath gives the heart room to remember:",
    "In the quiet of Sabbath, hold onto this:",
    "Let Sabbath worship bring this close:",
    "Sabbath rest makes space for one truth:",
    "At the Sabbath pause, receive this:",
    "Let the seventh-day Sabbath steady this truth:",
    "In Sabbath rest, return to this:",
)

LEGACY_THEME_REPLACEMENTS = {
    "The Surrendered Heart": "a surrendered heart",
    "Promises That Do Not Fail": "God's faithful promises",
    "Healing in His Presence": "healing in Christ's presence",
    "The Cross and Daily Grace": "daily life under the cross",
    "The Way, the Truth, and the Life": "the way of Jesus",
    "Peace in the Storm": "Christ's peace under pressure",
    "Rain down on me": "a prayer for renewal",
}

MONTH_ARC_PATTERN = re.compile(
    r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"(?:'s)?\s+(?:arc|theme)\b|\b(?:arc|theme)\s+(?:for|of)\s+"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\b|"
    r"\b(?:opens?|closes?|ends?)\s+"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\b|"
    r"\b(?:as\s+)?(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+(?:opens?|closes?|ends?)\b|"
    r"\b(?:first|last)\s+(?:truth|word|lesson|invitation)\s+of\s+"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\b",
    re.I,
)


TITLE_PREFIXES = (
    "Let Mercy Speak ",
    "Let Peace Lead ",
    "Let Grace Form ",
    "Let Fire Refine ",
    "Let Hope Rise ",
    "Let Love Teach ",
    "Wake Up to ",
    "Come Home to ",
    "Hold Fast to ",
    "Lean Into ",
    "Listen for ",
    "Practice ",
    "Surrender to ",
    "Remember ",
    "Discover ",
    "Receive ",
    "Embrace ",
    "Awaken ",
    "Return to ",
    "See Again ",
    "Walk in ",
    "Stand in ",
    "Behold ",
    "Follow ",
    "Rest in ",
    "Choose ",
    "Anchor ",
    "Breathe ",
    "Carry ",
    "Trust ",
    "Yield to ",
)


TITLE_PATTERNS = {
    1: (
        "Love Has the First Word",
        "Already Held by the Father",
        "When {core} Reaches the {image}",
        "Grace for the {image}",
        "The Father Meets You at the {image}",
        "Belonging Before the Battle",
        "What Mercy Says in the {image}",
        "No Audition at the Father's Door",
        "The Love That Stays",
        "Where Fear Loses Its Claim",
        "A Faithful Hand for the {image}",
        "Still Chosen in the {image}",
        "The Welcome You Did Not Earn",
        "Mercy for the Road Ahead",
        "Let {core} Become Real",
        "Kept While You Are Still Becoming",
    ),
    2: (
        "Jesus Is Already on the Road",
        "When the Teacher Calls You Closer",
        "Follow Him Through the {image}",
        "The Next Faithful Step",
        "At the Table with Jesus",
        "Where His Voice Finds You",
        "The Road That Forms a Disciple",
        "Grace for the {image}",
        "Near Enough to Be Changed",
        "When Admiration Becomes Surrender",
        "Walking the Truth in Love",
        "Jesus in the Ordinary Place",
        "A Courage Shaped Like Christ",
        "Stay with Him in the {image}",
        "The Mercy Beside the Road",
        "Likeness to Jesus Is Enough",
    ),
    3: (
        "When the Spirit Enters the {image}",
        "Filled for the Work in Front of You",
        "Holy Power, Open Hands",
        "The Comforter in the {image}",
        "Where the Wind of God Leads",
        "Fire That Makes the Heart Clean",
        "The Presence You Cannot Manufacture",
        "Wisdom for the Ordinary Work",
        "When Prayer Goes Deeper Than Words",
        "Fruit Before Display",
        "The Spirit Is Near in the {image}",
        "Freedom for the Hidden Place",
        "Power Under the Lordship of Jesus",
        "Fresh Oil for the Road Ahead",
        "A Filled Life Begins with Surrender",
        "Comfort for the Long Night",
    ),
}


CLOSING_PATTERNS = {
    1: (
        "You are not auditioning for a place in God's heart. Receive {theme}, then let that love shape your next honest yes.",
        "The Father is not waiting for a polished version of you at the {image}. He is asking for the real heart He already loves.",
        "Fear may describe the moment, but it does not get to name you. Let {theme} have the final word today.",
        "Grace is not permission to stay unchanged; it is power to stop hiding. Step into {theme} with both honesty and hope.",
        "The Father's love is tender enough to hold you and strong enough to lead you. Follow that love into the next faithful choice.",
        "You do not need every answer before you can trust the Father's heart. Begin with the mercy already in front of you.",
    ),
    2: (
        "Jesus is not asking for admiration from a distance. Let {theme} become one faithful step beside Him today.",
        "The road with Jesus is not always easy, but it is never empty. He is already present at the {image}.",
        "Do not wait for a dramatic moment to follow. The next Christlike response is holy enough to begin.",
        "Grace brings you close, and closeness changes how you walk. Stay near Jesus when the next choice arrives.",
        "The voice of fear may be loud, but it is not your shepherd. Let the words of Jesus set the pace today.",
        "Following Jesus becomes real where love costs something. Take the honest step and trust Him with the fruit.",
    ),
    3: (
        "The Holy Spirit does not fill a life for display. Yield the {image}, and let His presence become faithful obedience.",
        "You do not have to manufacture what only God can give. Open your hands to {theme} and receive the next instruction.",
        "Holy power is safest in a surrendered heart. Ask the Spirit to make Jesus visible in the way you respond today.",
        "The Comforter is not absent from the hidden place. Invite Him into the part you have been carrying alone.",
        "The Spirit's work is deeper than a moment of emotion. Let {theme} become fruit someone else can actually feel.",
        "Where your strength ends, dependence can begin. Welcome the Spirit into the {image} without pretending you are fine.",
    ),
}


IMAGE_WORDS = (
    ("wilderness", "wilderness"),
    ("river", "river"),
    ("water", "waters"),
    ("fire", "fire"),
    ("wind", "wind"),
    ("door", "doorway"),
    ("road", "road"),
    ("way", "road"),
    ("path", "path"),
    ("table", "table"),
    ("bread", "table"),
    ("light", "light"),
    ("dark", "night"),
    ("night", "night"),
    ("morning", "morning"),
    ("mountain", "mountain"),
    ("rock", "rock"),
    ("house", "house"),
    ("home", "threshold"),
    ("field", "field"),
    ("seed", "field"),
    ("harvest", "harvest"),
    ("shepherd", "pasture"),
    ("sheep", "pasture"),
    ("hand", "open hand"),
    ("heart", "heart"),
    ("voice", "quiet place"),
    ("garment", "covering"),
    ("oil", "anointing"),
    ("rain", "rain"),
    ("storm", "storm"),
    ("sea", "shore"),
    ("cross", "crossroads"),
)


BANNED_SENTENCE_FRAGMENTS = (
    "take one surrendered step before worry gets the first word",
    "let prayer turn insight into obedience before noon",
    "let prayer turn insight into obedience today",
    "start from what god has revealed, not from what the day is demanding",
    "do not rush past the verse; let it steady you before you move",
    "let the spirit press this from information into formation",
    "this day falls on saturday, the seventh-day sabbath in the 2026 production calendar",
    "this day falls on the seventh-day sabbath in the 2026 production calendar",
    "in the 2026 production calendar",
    "walk out of this page with courage, tenderness, and clarity",
    "receive the truth deeply enough that it changes your next decision",
    "the day does not get to name you before god does",
    "carry this like bread for the road, not decoration for the shelf",
    "let this word give your morning a spine and your heart a place to rest",
)


LANGUAGE_TERMS = {
    "ahavah", "akoloutheo", "anastasis", "didaskalos", "dunamis", "eirene", "emunah",
    "gaal", "hesed", "hodos", "kyrios", "lev", "meno", "nacham", "parakletos", "phos",
    "pneuma", "qavah", "rachamim", "shalom", "shamar", "sozo", "splagchnizomai", "yada",
}


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cleaned = "\n".join(line.rstrip() for line in content.rstrip().splitlines())
    path.write_text(cleaned + "\n", encoding="utf-8")


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_usfm(text: str) -> str:
    text = re.sub(r"\\f\s+.*?\\f\*", "", text, flags=re.S)
    text = re.sub(r"\\x\s+.*?\\x\*", "", text, flags=re.S)
    for _ in range(3):
        text = re.sub(r"\\\+?w\s+([^|\\]+)\|.*?\\\+?w\*", r"\1", text, flags=re.S)
    for marker in ("add", "nd", "wj", "bk", "k", "qt"):
        text = re.sub(rf"\\{marker}\s+(.*?)\\{marker}\*", r"\1", text, flags=re.S)
    text = re.sub(r"\\[+a-z0-9]+\*?(?:\s+)?", " ", text, flags=re.I)
    text = text.replace("¶", "")
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"\s+([,.;:?!])", r"\1", text)


def load_kjv() -> dict[str, str]:
    if not KJV_ZIP.exists():
        raise SystemExit(f"KJV source missing: {KJV_ZIP}")
    verses: dict[str, str] = {}
    with zipfile.ZipFile(KJV_ZIP) as archive:
        for member in archive.namelist():
            match = re.search(r"-([123]?[A-Z]{2,3})eng-kjv2006\.usfm$", member)
            if not match or match.group(1) not in BOOK_CODES:
                continue
            book = BOOK_CODES[match.group(1)]
            chapter = 0
            current_verse: int | None = None
            current_parts: list[str] = []

            def flush() -> None:
                if current_verse is None:
                    return
                cleaned = clean_usfm(" ".join(current_parts))
                if cleaned:
                    verses[f"{book} {chapter}:{current_verse}"] = cleaned

            raw = archive.read(member).decode("utf-8-sig", errors="replace")
            for line in raw.splitlines():
                chapter_match = re.match(r"\\c\s+(\d+)", line)
                verse_match = re.match(r"\\v\s+(\d+)\s+(.*)", line)
                if chapter_match:
                    flush()
                    chapter = int(chapter_match.group(1))
                    current_verse = None
                    current_parts = []
                elif verse_match:
                    flush()
                    current_verse = int(verse_match.group(1))
                    current_parts = [verse_match.group(2)]
                elif current_verse is not None:
                    current_parts.append(line)
            flush()
    return verses


def parse_reference(reference: str) -> tuple[str, int, int]:
    match = re.match(r"^(.+?)\s+(\d+):(\d+)$", reference.strip())
    if not match:
        raise ValueError(f"Unsupported Scripture reference: {reference}")
    book = {"Psalms": "Psalm", "Song of Songs": "Song of Solomon"}.get(match.group(1), match.group(1))
    return book, int(match.group(2)), int(match.group(3))


def parse_fields(raw: str) -> tuple[dict[str, str], list[str]]:
    fields: dict[str, str] = {}
    paragraphs: list[str] = []
    for part in re.split(r"\n\n+", raw.strip()):
        part = part.strip()
        if not part or part == "---" or part.startswith("<!--"):
            continue
        bold = re.match(r"^\*\*(.+?):\*\*\s*(.*)$", part, flags=re.S)
        if bold:
            label = bold.group(1).strip().lower()
            value = bold.group(2).strip()
            if label == "scripture reference":
                fields["scripture"] = value
            elif label in {"context and language lens", "production lens correction", "production lens", "scripture context"}:
                fields["lens"] = value
            elif label == "today step":
                fields["step"] = value
            elif label == "prayer":
                fields["prayer"] = value
            elif label == "journal prompt":
                fields["prompt"] = value
            elif label == "morning impact":
                fields["impact"] = value
            else:
                paragraphs.append(part)
        else:
            paragraphs.append(part)
    return fields, paragraphs


def parse_master(book: Book, kjv: dict[str, str]) -> list[Entry]:
    path = MASTER / f"volume-{book.volume}-master-interior-manuscript.md"
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r"^## (?P<head>(?:Day (?P<day>\d{3}) - (?P<date>.+?))|(?:Bonus(?: / Leap Day)? - (?P<bonus_date>.+?)))$",
        flags=re.M,
    )
    matches = list(pattern.finditer(text))
    entries: list[Entry] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        chunk = text[start:end].strip()
        title_match = re.match(r"^### (?P<title>.+?)\n\n(?P<body>.*)", chunk, flags=re.S)
        if not title_match:
            continue
        fields, paragraphs = parse_fields(title_match.group("body"))
        source_reference = fields.get("scripture", "")
        reference = re.sub(r"^Psalms\s+", "Psalm ", source_reference)
        ref_book, chapter, verse = parse_reference(reference)
        kjv_reference = f"{ref_book} {chapter}:{verse}"
        if kjv_reference not in kjv:
            raise ValueError(f"KJV text missing for {reference} (normalized as {kjv_reference})")
        original_day = float(int(match.group("day"))) if match.group("day") else 59.5
        original_date = (match.group("date") or match.group("bonus_date") or "").strip()
        entry = Entry(
            original_day=original_day,
            original_date=original_date,
            original_title=title_match.group("title").strip(),
            scripture=reference,
            lens=fields.get("lens", ""),
            body=paragraphs,
            step=fields.get("step", ""),
            prayer=fields.get("prayer", ""),
            prompt=fields.get("prompt", ""),
            impact=fields.get("impact", ""),
            source_heading=match.group("head"),
            source_scripture=source_reference,
            book=ref_book,
            chapter=chapter,
            verse=verse,
            scripture_text=kjv[kjv_reference],
        )
        entry.core = title_core(entry.original_title)
        entries.append(entry)
    if len(entries) != 366:
        raise ValueError(f"Volume {book.volume}: expected 366 entries, found {len(entries)}")
    return entries


def title_core(title: str) -> str:
    core = title.strip()
    for _ in range(4):
        matched = False
        for prefix in sorted(TITLE_PREFIXES, key=len, reverse=True):
            if core.lower().startswith(prefix.lower()):
                core = core[len(prefix) :].strip()
                matched = True
                break
        if not matched:
            break
    core = re.sub(r"^(?:let|see|stand|listen|walk|rest|refine)\s+", "", core, flags=re.I)
    core = re.sub(r"\b(?:finishing hope|grateful remembrance|holy steadiness|sabbath trust)\b", "", core, flags=re.I)
    core = re.sub(r"^(?:again|refine|through|in|for)\s+", "", core, flags=re.I)
    core = re.sub(r"\b(in|for|through)\s+\1\b", r"\1", core, flags=re.I)
    core = re.sub(r"\b(?:again)\b", "", core, flags=re.I)
    core = re.sub(r"^(the\s+)+", "", core, flags=re.I)
    core = re.sub(r"\s+", " ", core).strip(" .")
    if re.fullmatch(r"Father(?:'s)?", core, flags=re.I):
        core = "Father's Care"
    if re.fullmatch(r"Jesus(?:'s|'?)", core, flags=re.I):
        core = "Nearness of Jesus"
    return core or "grace for today"


def title_is_clean(title: str) -> bool:
    lower = re.sub(r"\s+", " ", title.lower()).strip()
    if re.search(
        r"\b(?:when let|let see|down talk|in again|the the|and and|to to|in in|for for|"
        r"that become|than become|finds become|at the road|at the waters|in the shore)\b|"
        r"^when (?:through|in|teach)\b|^let (?:through|in|teach|lead|speak|form|rest|stand|walk|carry)\b",
        lower,
    ):
        return False
    if re.search(r"\b(?:in in|for for|through through|let let|again)\b", lower):
        return False
    words = re.findall(r"[a-z']+", lower)
    if any(left == right for left, right in zip(words, words[1:])):
        return False
    if len(words) > 3 and words[-1] in words[:-2]:
        return False
    return True


def theme_score(entry: Entry, theme: Theme) -> int:
    text = " ".join([entry.original_title, entry.lens, *entry.body, entry.step, entry.prompt]).lower()
    score = 0
    for keyword in theme.keywords:
        score += 3 * len(re.findall(rf"\b{re.escape(keyword)}\w*\b", text))
        if keyword in entry.original_title.lower():
            score += 8
        if keyword in entry.lens.lower():
            score += 3
    return score


def assign_themes(book: Book, entries: list[Entry]) -> list[list[Entry]]:
    regular = [entry for entry in entries if entry.original_day != 59.5]
    capacities = [count for _, count in MONTHS]
    book_totals = Counter(entry.book for entry in regular)
    per_theme_book_caps = {name: (total + len(book.themes) - 1) // len(book.themes) for name, total in book_totals.items()}
    scored = []
    for entry in regular:
        scores = [theme_score(entry, theme) for theme in book.themes]
        scored.append((max(scores), sum(scores), entry, scores))
    scored.sort(key=lambda row: (-row[0], -row[1], row[2].original_day))
    assigned: list[list[Entry]] = [[] for _ in book.themes]
    remaining = capacities[:]
    theme_book_counts: list[Counter[str]] = [Counter() for _ in book.themes]
    for _, _, entry, scores in scored:
        candidates = [index for index, value in enumerate(remaining) if value > 0]
        balanced_candidates = [
            index for index in candidates
            if theme_book_counts[index][entry.book] < per_theme_book_caps[entry.book]
        ]
        if balanced_candidates:
            candidates = balanced_candidates
        selected = max(
            candidates,
            key=lambda index: (
                scores[index] * 5 - theme_book_counts[index][entry.book] * 25,
                remaining[index] / capacities[index],
                -abs(index - int((entry.original_day - 1) // 31)),
                -index,
            ),
        )
        entry.assigned_theme = selected
        assigned[selected].append(entry)
        theme_book_counts[selected][entry.book] += 1
        remaining[selected] -= 1
    if any(remaining):
        raise ValueError(f"Volume {book.volume}: theme capacity mismatch {remaining}")
    return assigned


def schedule_theme(entries: list[Entry], theme_index: int) -> list[Entry]:
    by_book: dict[str, list[Entry]] = defaultdict(list)
    for entry in entries:
        by_book[entry.book].append(entry)
    total_entries = len(entries)
    total_by_book = {name: len(items) for name, items in by_book.items()}
    used_by_book: Counter[str] = Counter()
    scheduled: list[Entry] = []
    previous_book = ""
    previous_chapter = -1
    previous_core = ""
    while by_book:
        selected_book = max(
            by_book,
            key=lambda name: (
                total_by_book[name] * (len(scheduled) + 1) / total_entries - used_by_book[name],
                int(name != previous_book),
                int(hashlib.sha256(f"{theme_index}:{name}:{len(scheduled)}".encode()).hexdigest()[:8], 16),
            ),
        )

        def candidate_score(entry: Entry) -> tuple[int, int, int]:
            chapter_change = int(entry.chapter != previous_chapter or entry.book != previous_book)
            core_change = int(entry.core.lower() != previous_core)
            stable_jitter = int(hashlib.sha256(f"{theme_index}:{entry.scripture}".encode()).hexdigest()[:8], 16)
            return chapter_change, core_change, stable_jitter

        selected = max(by_book[selected_book], key=candidate_score)
        by_book[selected_book].remove(selected)
        if not by_book[selected_book]:
            del by_book[selected_book]
        scheduled.append(selected)
        used_by_book[selected_book] += 1
        previous_book = selected.book
        previous_chapter = selected.chapter
        previous_core = selected.core.lower()
    return scheduled


def verse_image(entry: Entry) -> str:
    text = entry.scripture_text.lower()
    for needle, image in IMAGE_WORDS:
        if re.search(rf"\b{re.escape(needle)}\w*\b", text):
            return image
    fallbacks = ("threshold", "quiet place", "road", "open hand", "hidden place", "ordinary day")
    digest = int(hashlib.sha256(entry.scripture.encode()).hexdigest()[:8], 16)
    return fallbacks[digest % len(fallbacks)]


def verse_fragment(entry: Entry) -> str:
    stopwords = {
        "about", "after", "again", "against", "also", "among", "because", "before", "being",
        "came", "come", "could", "did", "does", "every", "from", "gave", "give", "given",
        "hath", "have", "having", "into", "itself", "made", "make", "many", "more", "most",
        "neither", "other", "over", "same", "shall", "should", "than", "that", "their", "them",
        "there", "therefore", "these", "they", "this", "those", "through", "unto", "upon", "very",
        "were", "what", "when", "where", "which", "while", "whom", "whose", "will", "with", "would",
        "your", "yours", "thee", "thou", "thy", "ye", "and", "but", "for", "not", "the", "was",
    }
    words = re.findall(r"[A-Za-z']+", entry.scripture_text)
    content = [word for word in words if len(word) > 3 and word.lower() not in stopwords]
    if not content:
        return entry.core
    return " ".join(content[:4]).title()


def sabbath_context_allowed(book: Book, entry: Entry) -> bool:
    theme = book.themes[entry.assigned_theme]
    scripture = entry.scripture_text.lower()
    return bool(
        re.search(r"\bsabbath\b|\bseventh day\b", scripture)
        or "sabbath" in theme.keywords
        or "rest" in theme.keywords
    )


def replace_legacy_journey_language(text: str) -> str:
    for old, new in LEGACY_THEME_REPLACEMENTS.items():
        text = re.sub(rf"\b{re.escape(old)}\b", new, text, flags=re.I)
    return text


def neutralize_inherited_sabbath_language(text: str) -> str:
    pauses = (
        "an unhurried moment with God",
        "a quiet pause for prayer",
        "time set apart with God",
        "a slower rhythm of worship",
        "a deliberate moment of trust",
        "a quiet place before God",
    )
    seed = int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)
    pause = pauses[seed % len(pauses)]
    replacements = (
        (r"\b(?:this\s+)?Saturday\s+Sabbath(?:\s+rest)?\b", pause),
        (r"\bOn this (?:Saturday )?Sabbath\b", "Today"),
        (r"\bthis Sabbath\b", "today"),
        (r"\bDuring Sabbath rest\b", f"During {pause}"),
        (r"\bIn the quiet of Sabbath\b", f"In {pause}"),
        (r"\bAt the Sabbath pause\b", f"In {pause}"),
        (r"\bLet Sabbath worship\b", "Let worship"),
        (r"\bSabbath worship\b", "worship"),
        (r"\bSabbath rest\b", pause),
        (r"\bthe seventh-day Sabbath\b", pause),
        (r"\bseventh-day Sabbath\b", pause),
        (r"\bSabbath trust\b", "quiet trust"),
        (r"\bSabbath peace\b", "settled peace"),
        (r"\bSabbath-rooted\b", "grace-rooted"),
        (r"\bSabbath grace\b", "restful grace"),
        (r"\bSabbath\b", "rest"),
    )
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text, flags=re.I)
    return text


def stale_journey_sentence(book: Book, entry: Entry, sentence: str) -> bool:
    if MONTH_ARC_PATTERN.search(sentence):
        return True
    if not sabbath_context_allowed(book, entry) and re.search(
        r"\bSabbath\b|\bseventh[- ]day\b",
        sentence,
        flags=re.I,
    ):
        return True
    return False


def clean_journey_field(book: Book, entry: Entry, text: str) -> str:
    text = replace_legacy_journey_language(text)
    if not sabbath_context_allowed(book, entry):
        text = neutralize_inherited_sabbath_language(text)
    text = re.sub(r"\bSaturday\s+", "", text, flags=re.I)
    return " ".join(
        sentence
        for sentence in split_sentences(text)
        if not stale_journey_sentence(book, entry, sentence)
    )


def clean_sentence_text(text: str) -> str:
    text = replace_legacy_journey_language(text)
    text = text.replace("\u2011", "-").replace("\u2014", "-")
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\bPsalms(?=\s+\d+(?::\d+)?)", "Psalm", text)
    text = re.sub(r"\bthis month\b", "in this season", text, flags=re.I)
    text = re.sub(r"\bMatthew 18:11, where included,", "Matthew 18:11", text, flags=re.I)
    text = re.sub(
        r"Even with textual-placement review still ahead, the theme harmonizes with the surrounding chapter's concern for little ones, humility, and the Father's care\.",
        "The surrounding chapter also holds little ones, humility, and the Father's care together.",
        text,
        flags=re.I,
    )
    text = re.sub(r"\btextual-placement review\b", "context review", text, flags=re.I)
    text = re.sub(r"\bFor Adventist readers, this matters deeply:\s*", "This matters because ", text, flags=re.I)
    text = re.sub(r"\brest this Saturday Sabbath\b", "rest today", text, flags=re.I)
    text = re.sub(r"\bon this (?:Saturday )?Sabbath\b", "during Sabbath rest", text, flags=re.I)
    text = re.sub(r"\bthis Saturday Sabbath\b", "during Sabbath rest", text, flags=re.I)
    text = re.sub(r"\bSaturday Sabbath\b", "seventh-day Sabbath", text, flags=re.I)
    text = re.sub(r"\bon this Sabbath\b", "in Sabbath rest", text, flags=re.I)
    text = re.sub(r"\bthis Sabbath\b", "Sabbath rest", text, flags=re.I)
    text = re.sub(r"\bas this year closes\b", "as this season closes", text, flags=re.I)
    text = re.sub(r"\bbefore the year ends\b", "before this season ends", text, flags=re.I)
    text = re.sub(r"\bfrom this year\b", "from this season", text, flags=re.I)
    text = re.sub(r"\bfor the year ahead\b", "for the season ahead", text, flags=re.I)
    text = re.sub(r"\bthe fruit of this year\b", "the fruit of this season", text, flags=re.I)
    text = re.sub(r"\bat the end of a year\b", "at the end of a demanding season", text, flags=re.I)
    text = re.sub(r"\bthe end of a year\b", "a demanding season", text, flags=re.I)
    text = re.sub(r"\bcloses the year\b", "closes a demanding season", text, flags=re.I)
    text = re.sub(r"\bending the year\b", "finishing a demanding season", text, flags=re.I)
    text = re.sub(r"\byear-ending\b", "season-closing", text, flags=re.I)
    text = re.sub(r"\bthe year can close\b", "a season can close", text, flags=re.I)
    text = re.sub(r"\bclose the year\b", "move forward", text, flags=re.I)
    text = re.sub(r"\bclosing the year\b", "moving forward", text, flags=re.I)
    text = re.sub(r"\bClose it by\b", "Move forward by", text)
    text = re.sub(r"\bcloses this month\b", "brings this movement to a close", text, flags=re.I)
    text = re.sub(r"\bclose this month\b", "bring this movement to a close", text, flags=re.I)
    text = re.sub(r"\bthe first day of this new month\b", "this new beginning", text, flags=re.I)
    text = re.sub(r"\bfirst day of this new month\b", "this new beginning", text, flags=re.I)
    text = re.sub(r"\bthis year\b", "this season", text, flags=re.I)
    text = re.sub(r"\byear-end\b", "seasonal", text, flags=re.I)
    text = re.sub(r"\bbefore noon\b", "today", text, flags=re.I)
    text = re.sub(r"([.!?])([\"'])[.,]", r"\1\2", text)
    text = re.sub(r"\.{4,}", "...", text)
    return text


def split_sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", clean_sentence_text(text)) if part.strip()]


def clean_body(book: Book, entry: Entry) -> list[str]:
    sentences: list[str] = []
    seen: set[str] = set()
    for paragraph in entry.body:
        paragraph = re.sub(re.escape(entry.original_title), "the Scripture's invitation", paragraph, flags=re.I)
        paragraph = re.sub(r"\bPractice this truth\b", "Practice the Scripture's invitation", paragraph, flags=re.I)
        paragraph = re.sub(r"\bReceive this truth\b", "Receive the Scripture's invitation", paragraph, flags=re.I)
        paragraph = re.sub(r"\bLet this truth\b", "Let the Scripture's invitation", paragraph, flags=re.I)
        paragraph = re.sub(r"\b[Tt]his truth\b", "the Scripture's invitation", paragraph)
        paragraph = re.sub(r"\bthe Scripture's invitation by\b", "Practice the Scripture's invitation by", paragraph, flags=re.I)
        paragraph = re.sub(
            r"\bthe Scripture's invitation (today|in|for|through|when|where|before|after|as)\b",
            r"Practice the Scripture's invitation \1",
            paragraph,
            flags=re.I,
        )
        paragraph = re.sub(
            r"\broom to the Scripture's invitation\b",
            "room to receive the Scripture's invitation",
            paragraph,
            flags=re.I,
        )
        paragraph = re.sub(
            r"^The Scripture's invitation (in\b[^.?!]*?\bby\b)",
            r"Practice the Scripture's invitation \1",
            paragraph,
            flags=re.I,
        )
        paragraph = re.sub(r"\bReceive\s+Practice the Scripture's invitation\b", "Practice the Scripture's invitation", paragraph, flags=re.I)
        paragraph = re.sub(
            r"\bTo the Scripture's invitation is\b",
            "The Scripture's invitation is",
            paragraph,
            flags=re.I,
        )
        paragraph = re.sub(
            r"\bPractice the Scripture's invitation in you by\b",
            "Let the Scripture's invitation shape you by",
            paragraph,
            flags=re.I,
        )
        paragraph = re.sub(
            r"\bPractice the Scripture's invitation in you\b",
            "Let the Scripture's invitation take root in you",
            paragraph,
            flags=re.I,
        )
        paragraph = re.sub(r"\bheart Practice\b", "heart practice", paragraph)
        paragraph = re.sub(
            r"This rest helps the heart practice the Scripture's invitation in",
            "This rest helps the heart receive God's grace through",
            paragraph,
            flags=re.I,
        )
        paragraph = re.sub(
            r"\bThe Scripture's invitation\.",
            "Receive the Scripture's invitation with an honest response.",
            paragraph,
            flags=re.I,
        )
        paragraph = re.sub(
            r"\bThe Scripture's invitation over\b",
            "Let the Scripture's invitation speak over",
            paragraph,
            flags=re.I,
        )
        paragraph = re.sub(
            r"\bThe Scripture's invitation into\b",
            "Carry the Scripture's invitation into",
            paragraph,
            flags=re.I,
        )
        for sentence in split_sentences(paragraph):
            sentence = sentence[:1].upper() + sentence[1:] if sentence else sentence
            if stale_journey_sentence(book, entry, sentence):
                continue
            lower = sentence.lower()
            first_word = re.match(r"^([a-z][a-z'-]+)", lower)
            if (
                "`" in sentence
                or re.search(r"\b(?:the Hebrew|the Greek|the Aramaic|Hebrew word|Greek word)\b", sentence, flags=re.I)
                or any(re.search(rf"\b{re.escape(term)}\b", lower) for term in LANGUAGE_TERMS)
                or (first_word and first_word.group(1) in LANGUAGE_TERMS and re.search(r"\b(?:means|is|names|points|speaks)\b", lower))
            ):
                continue
            if re.search(
                r"\b(?:translation review note|permissions review|editorial note|"
                r"final wording and placement|production batch|production date|AI model|"
                r"language model|generated prompt|prompt pack|voice filter)\b",
                sentence,
                flags=re.I,
            ):
                continue
            if re.search(r"\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|2026)\b", sentence, flags=re.I):
                continue
            if re.search(r"\b(?:opens|opened)\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\b", sentence, flags=re.I):
                continue
            if re.search(r"\bfirst day of (?:a new month|the month|January|February|March|April|May|June|July|August|September|October|November|December)\b", sentence, flags=re.I):
                continue
            if re.search(r"\b(?:dated entry|production date|2026 production calendar)\b", sentence, flags=re.I):
                continue
            if any(fragment in lower for fragment in BANNED_SENTENCE_FRAGMENTS):
                continue
            transition_seed = int(
                hashlib.sha256(f"transition:{entry.source_scripture}:{sentence}".encode()).hexdigest()[:8],
                16,
            )
            sentence = re.sub(
                r"Practice the Scripture's invitation by",
                INVITATION_TRANSITIONS[transition_seed % len(INVITATION_TRANSITIONS)],
                sentence,
                flags=re.I,
            )
            sentence = re.sub(
                r"Sabbath rest can remind us:",
                SABBATH_TRANSITIONS[transition_seed % len(SABBATH_TRANSITIONS)],
                sentence,
                flags=re.I,
            )
            if lower in {
                "that matters in the morning.",
                "this is deeply practical.",
                "practice this truth.",
                "receive this truth.",
                "this truth.",
            }:
                continue
            if sentence.startswith("<!--") or sentence == "---":
                continue
            normalized = re.sub(r"[^a-z0-9]+", " ", lower).strip()
            if normalized in seen:
                continue
            seen.add(normalized)
            sentences.append(sentence)

    if not sentences:
        sentences = ["God meets the surrendered heart with truth, mercy, and a faithful invitation to take the next step."]

    max_words = 285
    selected: list[str] = []
    word_total = 0
    for sentence in sentences:
        words = len(sentence.split())
        if word_total + words <= max_words or len(selected) < 5:
            selected.append(sentence)
            word_total += words
    for sentence in sentences[-2:]:
        if sentence not in selected and word_total + len(sentence.split()) <= max_words + 20:
            selected.append(sentence)
            word_total += len(sentence.split())

    target = max(1, sum(len(sentence.split()) for sentence in selected) // 4)
    paragraphs: list[str] = []
    current: list[str] = []
    current_words = 0
    remaining_groups = 4
    for sentence in selected:
        current.append(sentence)
        current_words += len(sentence.split())
        remaining_sentences = len(selected) - sum(len(split_sentences(p)) for p in paragraphs) - len(current)
        if remaining_groups > 1 and current_words >= target and remaining_sentences >= remaining_groups - 1:
            paragraphs.append(" ".join(current))
            current = []
            current_words = 0
            remaining_groups -= 1
    if current:
        paragraphs.append(" ".join(current))
    while len(paragraphs) > 4:
        tail = paragraphs.pop()
        paragraphs[-1] = f"{paragraphs[-1]} {tail}"
    while len(paragraphs) < 4:
        longest_index = max(range(len(paragraphs)), key=lambda index: len(paragraphs[index].split()))
        parts = split_sentences(paragraphs[longest_index])
        if len(parts) < 2:
            break
        midpoint = max(1, len(parts) // 2)
        paragraphs[longest_index : longest_index + 1] = [" ".join(parts[:midpoint]), " ".join(parts[midpoint:])]
    return paragraphs


OPENBIBLE_GOSPEL_CODES = {
    "Matt": "Matthew",
    "Mark": "Mark",
    "Luke": "Luke",
    "John": "John",
}

GOSPEL_MATCH_STOPWORDS = {
    "the", "and", "but", "for", "that", "this", "with", "from", "into", "unto",
    "upon", "then", "than", "there", "their", "them", "they", "shall", "will",
    "would", "should", "could", "have", "hath", "has", "had", "been", "being",
    "were", "was", "are", "is", "not", "his", "him", "her", "she", "our", "you",
    "your", "thee", "thou", "thy", "who", "whom", "whose", "which", "what", "when",
    "where", "therefore", "also", "all", "any", "some", "one", "every", "out", "over",
}


def parse_openbible_reference(reference: str) -> str:
    match = re.match(r"^([1-3]?[A-Za-z]+)\.(\d+)\.(\d+)", reference)
    if not match or match.group(1) not in OPENBIBLE_GOSPEL_CODES:
        return ""
    return f"{OPENBIBLE_GOSPEL_CODES[match.group(1)]} {match.group(2)}:{match.group(3)}"


def load_gospel_cross_references() -> dict[str, dict[str, int]]:
    """Load the attributed OpenBible graph used to identify Gospel parallels."""
    if not CROSS_REFERENCES_ZIP.exists():
        raise SystemExit(f"Cross-reference source missing: {CROSS_REFERENCES_ZIP}")
    graph: dict[str, dict[str, int]] = defaultdict(dict)
    with zipfile.ZipFile(CROSS_REFERENCES_ZIP) as archive:
        lines = archive.read("cross_references.txt").decode("utf-8").splitlines()[1:]
    for line in lines:
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        left = parse_openbible_reference(parts[0])
        right = parse_openbible_reference(parts[1])
        if not left or not right or left == right:
            continue
        votes = int(parts[2])
        graph[left][right] = max(votes, graph[left].get(right, -999))
        graph[right][left] = max(votes, graph[right].get(left, -999))
    return graph


def gospel_match_words(text: str) -> list[str]:
    return [
        word
        for word in re.findall(r"[a-z']+", text.lower())
        if len(word) > 2 and word not in GOSPEL_MATCH_STOPWORDS
    ]


def scripture_window(kjv: dict[str, str], reference: str, radius: int = 2) -> str:
    book, chapter, verse = parse_reference(reference)
    return " ".join(
        kjv.get(f"{book} {chapter}:{number}", "")
        for number in range(max(1, verse - radius), verse + radius + 1)
    )


def gospel_match_score(
    source_reference: str,
    candidate_reference: str,
    votes: int,
    pastoral_signal: str,
    kjv: dict[str, str],
) -> int:
    source_words = gospel_match_words(kjv[source_reference])
    candidate_words = gospel_match_words(kjv[candidate_reference])
    source_tokens = set(source_words)
    candidate_tokens = set(candidate_words)
    source_bigrams = set(zip(source_words, source_words[1:]))
    candidate_bigrams = set(zip(candidate_words, candidate_words[1:]))
    source_window_words = gospel_match_words(scripture_window(kjv, source_reference))
    candidate_window_words = gospel_match_words(scripture_window(kjv, candidate_reference))
    source_window_tokens = set(source_window_words)
    candidate_window_tokens = set(candidate_window_words)
    source_window_bigrams = set(zip(source_window_words, source_window_words[1:]))
    candidate_window_bigrams = set(zip(candidate_window_words, candidate_window_words[1:]))
    signal_tokens = set(gospel_match_words(pastoral_signal))
    return (
        votes * 2
        + len(source_tokens.intersection(candidate_tokens)) * 35
        + len(source_bigrams.intersection(candidate_bigrams)) * 110
        + len(source_window_tokens.intersection(candidate_window_tokens)) * 18
        + len(source_window_bigrams.intersection(candidate_window_bigrams)) * 45
        + len(signal_tokens.intersection(candidate_window_tokens)) * 12
    )


def replace_reference_language(text: str, old_reference: str, new_reference: str) -> str:
    if not text:
        return text
    old_book = old_reference.rsplit(" ", 1)[0]
    new_book = new_reference.rsplit(" ", 1)[0]
    text = text.replace(old_reference, new_reference)
    text = re.sub(
        rf"\b{re.escape(old_book)}(?:'s)? Gospel\b",
        f"{new_book}'s Gospel",
        text,
        flags=re.I,
    )
    text = re.sub(rf"\b{re.escape(old_book)}'s\b", f"{new_book}'s", text, flags=re.I)
    return text


def reassign_volume_2_scriptures(entries: list[Entry], kjv: dict[str, str]) -> None:
    """Replace strong Matthew rows with documented, close Gospel parallels.

    Only direct graph links with strong textual and pastoral overlap are
    eligible. Lower-confidence links remain in Matthew rather than forcing
    variety at the expense of semantic fidelity.
    """
    if not CROSS_REFERENCES_ZIP.exists():
        raise SystemExit(f"Cross-reference source missing: {CROSS_REFERENCES_ZIP}")
    graph = load_gospel_cross_references()
    target_caps = {"Mark": 110, "Luke": 110, "John": 110}
    conversion_target = 150
    excluded_sources = {
        "Matthew 12:10",
        "Matthew 17:20",
        "Matthew 20:30",
        "Matthew 21:15",
        "Matthew 21:28",
    }
    forced_parallels = {"Matthew 18:3": "Mark 10:15"}
    candidate_rows: list[tuple[int, int, str, str]] = []
    for entry_index, entry in enumerate(entries):
        if entry.book != "Matthew":
            continue
        if entry.scripture in excluded_sources:
            continue
        pastoral_signal = " ".join([entry.lens, *entry.body, entry.step, entry.prompt])
        for candidate_reference, votes in graph.get(entry.scripture, {}).items():
            candidate_book, _, _ = parse_reference(candidate_reference)
            if candidate_book not in target_caps or candidate_reference not in kjv:
                continue
            forced = forced_parallels.get(entry.scripture)
            if forced and candidate_reference != forced:
                continue
            score = gospel_match_score(entry.scripture, candidate_reference, votes, pastoral_signal, kjv)
            if forced == candidate_reference:
                score += 100_000
            candidate_rows.append((score, entry_index, candidate_reference, candidate_book))

    assigned: dict[int, str] = {}
    used_references = {entry.scripture for entry in entries if entry.book != "Matthew"}
    target_counts: Counter[str] = Counter()
    for score, entry_index, candidate_reference, candidate_book in sorted(candidate_rows, reverse=True):
        if len(assigned) >= conversion_target:
            break
        if entry_index in assigned or candidate_reference in used_references:
            continue
        if target_counts[candidate_book] >= target_caps[candidate_book]:
            continue
        assigned[entry_index] = candidate_reference
        used_references.add(candidate_reference)
        target_counts[candidate_book] += 1
    if len(assigned) != conversion_target:
        raise ValueError(
            f"Volume 2 Gospel-parallel map produced {len(assigned)} of {conversion_target} required conversions"
        )

    for entry_index, new_reference in assigned.items():
        entry = entries[entry_index]
        old_reference = entry.scripture
        entry.lens = replace_reference_language(entry.lens, old_reference, new_reference)
        entry.body = [replace_reference_language(paragraph, old_reference, new_reference) for paragraph in entry.body]
        entry.step = replace_reference_language(entry.step, old_reference, new_reference)
        entry.prayer = replace_reference_language(entry.prayer, old_reference, new_reference)
        entry.prompt = replace_reference_language(entry.prompt, old_reference, new_reference)
        entry.impact = replace_reference_language(entry.impact, old_reference, new_reference)
        if old_reference == "Matthew 12:49" and new_reference == "Mark 3:34":
            entry.lens = re.sub(r"Jesus' gesture toward His disciples", "Jesus' look around at those seated near Him", entry.lens)
            entry.body = [
                re.sub(
                    r"Jesus stretching His hand toward His disciples",
                    "Jesus looking around at those seated near Him",
                    paragraph,
                )
                for paragraph in entry.body
            ]
        elif old_reference == "Matthew 13:22" and new_reference == "Mark 4:18":
            entry.body = [
                paragraph.replace(
                    "Mark 4:18 speaks of the word being crowded by the cares of the world and the deceitfulness of riches.",
                    "Mark 4:18 identifies those who hear the word; the next verse names the cares of this world and the deceitfulness of riches that choke it.",
                )
                for paragraph in entry.body
            ]
        elif old_reference == "Matthew 12:44" and new_reference == "Luke 11:25":
            entry.lens = entry.lens.replace("an empty house", "a swept and garnished house")
            replacements = {
                "The Shepherd's voice does more than empty a room.": "The Shepherd's voice does more than arrange a room.",
                "Luke 11:25 warns of a house swept, ordered, and still empty.": "Luke 11:25 finds the house swept and garnished.",
                "The image is sober because a life can look improved and still remain uninhabited by surrender.": "The surrounding warning is sober because external order is not the same as a life abiding in Christ.",
                "Empty space needs holy presence.": "A cleared room needs holy presence.",
            }
            for before, after in replacements.items():
                entry.body = [paragraph.replace(before, after) for paragraph in entry.body]
        elif old_reference == "Matthew 24:3" and new_reference == "Mark 13:4":
            entry.lens = entry.lens.replace(
                "The disciples coming to Jesus privately",
                "The disciples asking when Jesus' words will be fulfilled",
            )
            entry.body = [
                paragraph.replace(
                    "Mark 13:4 shows the disciples coming to Jesus privately with questions about what He has said.",
                    "Mark 13:4 records the disciples' question about when Jesus' words will be fulfilled and what sign will announce it.",
                )
                for paragraph in entry.body
            ]
        elif old_reference == "Matthew 21:23" and new_reference == "Luke 20:2":
            entry.body = [
                paragraph.replace(
                    "Luke 20:2 shows Jesus teaching in the temple when leaders challenge His authority.",
                    "Luke 20:2 records the leaders' direct challenge to Jesus' authority.",
                )
                for paragraph in entry.body
            ]
        entry.scripture = new_reference
        entry.book, entry.chapter, entry.verse = parse_reference(new_reference)
        entry.scripture_text = kjv[new_reference]


def remove_reused_body_sentences(paragraphs: list[str], used: set[str]) -> list[str]:
    """Keep the strongest first occurrence of inherited production boilerplate."""
    cleaned: list[str] = []
    for paragraph in paragraphs:
        retained: list[str] = []
        for sentence in split_sentences(paragraph):
            normalized = re.sub(r"[^a-z0-9]+", " ", sentence.lower()).strip()
            if len(normalized.split()) >= 8 and normalized in used:
                continue
            if len(normalized.split()) >= 8:
                used.add(normalized)
            retained.append(sentence)
        if retained:
            cleaned.append(" ".join(retained))
    return cleaned or ["God meets the surrendered heart with truth, mercy, and a faithful invitation to take the next step."]


def lift_language_notes(entry: Entry) -> None:
    notes: list[str] = []
    retained: list[str] = []
    for paragraph in entry.body:
        paragraph_sentences: list[str] = []
        for sentence in split_sentences(paragraph):
            match = re.match(r"^([A-Za-z][A-Za-z'-]{2,})\s+(?:means|is)\b", sentence)
            is_language_note = bool(match and match.group(1).lower() in LANGUAGE_TERMS)
            if is_language_note or re.search(r"\b(?:the Hebrew|the Greek|the Aramaic)\b", sentence, flags=re.I):
                notes.append(sentence)
            else:
                paragraph_sentences.append(sentence)
        if paragraph_sentences:
            retained.append(" ".join(paragraph_sentences))
    if notes:
        entry.body = retained
        note = " ".join(notes)
        entry.lens = f"{entry.lens} {note}".strip()
        entry.context_label = "Word and context"


def extract_reader_closing(entry: Entry, used: set[str]) -> str:
    """Lift the day's own strongest final sentence into the send-off position."""
    if not entry.body:
        return "Let this Scripture become one honest response before the day is over."
    final_sentences = split_sentences(entry.body[-1])
    if not final_sentences:
        return "Let this Scripture become one honest response before the day is over."
    closing = final_sentences.pop().strip()
    if len(closing.split()) < 7 and final_sentences:
        closing = f"{final_sentences.pop()} {closing}"
    if final_sentences:
        entry.body[-1] = " ".join(final_sentences)
    else:
        entry.body.pop()
    normalized = re.sub(r"[^a-z0-9]+", " ", closing.lower()).strip()
    if normalized in used:
        closing = f"For '{entry.title},' hold onto this: {closing[:1].lower() + closing[1:]}"
        normalized = re.sub(r"[^a-z0-9]+", " ", closing.lower()).strip()
    used.add(normalized)
    return closing


def connection_reflection(book: Book, entry: Entry) -> str:
    theme = book.themes[entry.assigned_theme]
    promise = theme.promise.rstrip(".")
    promise = promise[:1].lower() + promise[1:]
    focus = theme.name
    patterns = (
        "Read {connection} beside {primary}. Its witness deepens the theme \"{focus}\" and strengthens the invitation to {promise}.",
        "{connection} brings another biblical witness to \"{focus}\"; alongside {primary}, it calls the heart to {promise}.",
        "The thread continues in {connection}: \"{focus}\" is not an isolated idea, but part of Scripture's invitation to {promise}.",
        "Place {connection} next to {primary}. Together, the passages deepen \"{focus}\" and ask you to {promise}.",
        "Scripture answers Scripture in {connection}, widening today's meditation on \"{focus}\" and its call to {promise}.",
        "The echo in {connection} keeps \"{focus}\" connected to the larger biblical story and invites you to {promise}.",
    )
    seed = int(hashlib.sha256(f"connection:{entry.scripture}:{entry.connection_reference}".encode()).hexdigest()[:8], 16)
    return patterns[seed % len(patterns)].format(
        connection=entry.connection_reference,
        primary=entry.scripture,
        focus=focus,
        promise=promise,
    )


def voice_expansion(book: Book, entry: Entry) -> str:
    candidates = [part.strip(" ,") for part in re.split(r"[;:.!?]|,(?=\s)", entry.scripture_text) if part.strip(" ,")]
    suitable = [part for part in candidates if 6 <= len(part.split()) <= 18]
    clause = suitable[0] if suitable else candidates[0]
    clause_words = clause.split()
    if len(clause_words) > 18:
        clause = " ".join(clause_words[:18]).rstrip(",") + "..."
    clause = re.sub(r"^And\s+", "", clause)
    theme = book.themes[entry.assigned_theme].name.lower()
    image = verse_image(entry)
    patterns = {
        1: (
            'Notice what the verse puts first: "{clause}." Under the title "{title}," this line brings {theme} into the {image}, where trust can replace anxious proving.',
            'Let the words come close: "{clause}." In "{title}," {theme} is not distant theology; it meets the real pressure carried into the {image}.',
            'Stay with the movement of the Scripture: "{clause}." The reading "{title}" turns {theme} from an idea into a way of standing, speaking, and choosing.',
            'Hear the steadiness in the verse: "{clause}." Through "{title}," the heart can meet {theme} in the {image}.',
        ),
        2: (
            'Do not hurry past the words: "{clause}." In "{title}," Jesus brings {theme} close enough to become a choice, a posture, and a step beside Him.',
            'Listen to what the passage places in front of you: "{clause}." At the {image}, "{title}" shows how {theme} reshapes the next room you enter.',
            'Let this phrase slow you down: "{clause}." Jesus uses the movement in "{title}" to make {theme} more than an idea admired from a distance.',
            'Hold the line of Scripture in your heart: "{clause}." In the {image}, "{title}" forms a disciple who can live truth with love.',
        ),
        3: (
            'Hold onto the words: "{clause}." Through "{title}," the Spirit brings {theme} into actual need and turns presence into faithful action.',
            'Notice the life inside the verse: "{clause}." At the {image}, "{title}" shows that {theme} is not decoration for a religious moment.',
            'Let the Scripture set the expectation: "{clause}." The movement in "{title}" invites dependence on the Spirit for {theme}, not an imitation of spiritual power.',
            'Stay with this line: "{clause}." In the {image}, "{title}" holds truth with humility and power with love.',
        ),
    }
    seed = int(hashlib.sha256(f"voice:{entry.scripture}".encode()).hexdigest()[:8], 16)
    return patterns[book.volume][seed % len(patterns[book.volume])].format(
        clause=clause,
        theme=theme,
        image=image,
        title=entry.title,
    )


def clean_lens(book: Book, entry: Entry) -> tuple[str, str]:
    lens = clean_sentence_text(entry.lens)
    lens = re.sub(r"^(This lens|The production lens)\s+(keeps|reads|treats|uses|opens)\s+", "", lens, flags=re.I)
    lens = re.sub(r"^The architecture assigns?[^;]+;\s*", "", lens, flags=re.I)
    lens = re.sub(r"\bthe devotional focus is\b", "the focus is", lens, flags=re.I)
    lens = re.sub(r"\s+because the verse\s+", ". This verse ", lens, flags=re.I)
    lens = re.sub(r"\s+-\s*\.", ".", lens)
    sentences = [
        sentence
        for sentence in split_sentences(lens)
        if "`" not in sentence
        and not re.search(r"\b(?:Hebrew|Greek|Aramaic)\b", sentence, flags=re.I)
        and not re.search(r"\b(?:architecture|production date|dated entry|2026 production calendar)\b", sentence, flags=re.I)
        and not re.search(r"\b(?:opens|opened)\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\b", sentence, flags=re.I)
        and not any(re.match(rf"^{re.escape(term)}(?:/\w+)?\b", sentence, flags=re.I) for term in LANGUAGE_TERMS)
        and not stale_journey_sentence(book, entry, sentence)
    ]
    sentences = [sentence[:1].upper() + sentence[1:] if sentence else sentence for sentence in sentences[:2]]
    lens = " ".join(sentences).strip()
    words = lens.split()
    if len(words) > 42:
        lens = " ".join(words[:42]).rstrip(",;:") + "."
    return "Scripture context", lens


def deepen_entry(book: Book, entry: Entry) -> None:
    """Add one passage-specific pastoral movement where the source draft is too thin."""
    if book.volume not in DEEPENING_COUNSEL:
        return
    # Preserve the entry's own pastoral movement whenever it is already
    # substantial. The expansion is a rescue for genuinely thin readings,
    # not a trilogy-wide layer of repeated editorial scaffolding.
    if len(" ".join(entry.body).split()) >= 100:
        return
    theme = book.themes[entry.assigned_theme]
    counsel = DEEPENING_COUNSEL[book.volume][entry.assigned_theme]
    clauses = [part.strip(" ,") for part in re.split(r"[;:.!?]|,(?=\s)", entry.scripture_text) if part.strip(" ,")]
    clause = next((part for part in clauses if 6 <= len(part.split()) <= 18), clauses[0])
    clause = re.sub(r"^And\s+", "", clause)
    if len(clause.split()) > 18:
        clause = " ".join(clause.split()[:18]).rstrip(",") + "..."
    action = entry.step.rstrip(". ")
    action = action[:1].lower() + action[1:] if action else "take one honest step in response"
    openers = (
        'Stay with the verse\'s own words: "{clause}."',
        'The passage becomes personal in the line, "{clause}."',
        'One phrase deserves an unhurried hearing: "{clause}."',
        'The verse places its truth in front of us: "{clause}."',
        'Listen again to the movement of the text: "{clause}."',
        'The reading turns on these words: "{clause}."',
        'The Scripture brings the moment into focus: "{clause}."',
        'Let this part of the verse come close: "{clause}."',
        'The heart of the passage can be heard here: "{clause}."',
        'Do not hurry past the words, "{clause}."',
        'The verse gives the day a clear center: "{clause}."',
        'Hear the weight carried by this line: "{clause}."',
        'A close reading begins with the words, "{clause}."',
        'The passage asks for attention at this point: "{clause}."',
        'Let the Scripture slow the moment down: "{clause}."',
        'Return once more to the phrase, "{clause}."',
    )
    applications = (
        "That matters because {counsel}.",
        "In ordinary life, {counsel}.",
        "The invitation reaches beyond understanding: {counsel}.",
        "This is where faith becomes visible: {counsel}.",
        "For the life in front of you, {counsel}.",
        "The passage presses gently toward practice: {counsel}.",
        "Here is the pastoral weight of the text: {counsel}.",
        "The truth is not asking for performance; {counsel}.",
        "Let this shape the next decision: {counsel}.",
        "The deeper work begins as {counsel}.",
        "The words meet real pressure because {counsel}.",
        "This becomes more than an idea when {counsel}.",
        "The verse reaches the heart by showing that {counsel}.",
        "Its wisdom becomes lived truth as {counsel}.",
        "The reading calls for honesty because {counsel}.",
        "Grace takes practical shape when {counsel}.",
    )
    responses = (
        "Begin with one honest response: {action}.",
        "Put this into quiet practice: {action}.",
        "A small faithful answer is enough to begin: {action}.",
        "Carry the reading into one decision: {action}.",
        "Before the day moves on, {action}.",
        "Let prayer become action: {action}.",
        "Choose one concrete response: {action}.",
        "The next step can be simple: {action}.",
        "Answer the passage today: {action}.",
        "Make room for obedience: {action}.",
        "Let the truth enter the schedule: {action}.",
        "Take the reading with you: {action}.",
        "Practice the insight in one place: {action}.",
        "Give the passage a real answer: {action}.",
        "Move gently but clearly: {action}.",
        "Trust can start here: {action}.",
    )
    seed = int(hashlib.sha256(f"deepening:{book.volume}:{entry.scripture}".encode()).hexdigest()[:12], 16)
    paragraph = " ".join(
        (
            openers[seed % len(openers)].format(clause=clause),
            applications[(seed // 17) % len(applications)].format(counsel=counsel),
            responses[(seed // 271) % len(responses)].format(action=action),
        )
    )
    entry.body.append(clean_sentence_text(paragraph))


def apply_passage_body_rewrites(book: Book, entry: Entry) -> None:
    rewrite = PASSAGE_BODY_REWRITES.get((book.volume, entry.scripture))
    if rewrite:
        old, new = rewrite
        entry.body = [paragraph.replace(old, new) for paragraph in entry.body]
    if book.volume == 3 and entry.scripture == "Judges 6:5":
        entry.body = [
            paragraph.replace(
                "Oil for the waiting season closes in this season by reminding the heart that",
                "The waiting heart needs this reminder:",
            )
            for paragraph in entry.body
        ]


def clean_step(text: str) -> str:
    text = re.sub(r"^On this (?:Saturday )?Sabbath,\s*", "", text.strip(), flags=re.I)
    text = clean_sentence_text(text)
    text = re.sub(r"^(Today,\s*)+", "", text, flags=re.I)
    text = re.sub(r"^On this Sabbath,\s*", "", text, flags=re.I)
    if text:
        text = text[0].upper() + text[1:]
    if text and text[-1] not in ".!?" and not (text.endswith('"') and len(text) > 1 and text[-2] in ".!?"):
        text += "."
    return text


def clean_prompt(text: str) -> str:
    text = clean_sentence_text(text)
    text = re.sub(
        r"God's faithfulness Sabbath rest",
        "God's faithfulness during Sabbath rest",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"Christ's compassion as belonging Sabbath rest",
        "Christ's compassion as a place of belonging during Sabbath rest",
        text,
        flags=re.I,
    )
    if text and not text.endswith("?"):
        text = text.rstrip(".") + "?"
    if text.endswith("Sabbath rest?") and not re.search(
        r"\b(?:in|into|enter|during) Sabbath rest\?$",
        text,
        flags=re.I,
    ):
        text = re.sub(r" Sabbath rest\?$", " during Sabbath rest?", text)
    return text


def clean_prayer(text: str) -> str:
    text = clean_sentence_text(text)
    text = re.sub(
        r"\bteach me rest\s+([a-z])",
        lambda match: "teach me to rest in " + match.group(1),
        text,
        flags=re.I,
    )
    sentences = split_sentences(text)
    text = " ".join(sentence[:1].upper() + sentence[1:] if sentence else sentence for sentence in sentences)
    if text and not re.search(r"\bAmen\.?$", text, flags=re.I):
        text = text.rstrip(".") + ". Amen."
    return text


def revised_title(
    book: Book,
    entry: Entry,
    used: set[str],
    ending_use: Counter[str],
    recent_endings: list[str],
    subject_use: Counter[str],
    recent_subjects: list[str],
) -> str:
    theme = book.themes[entry.assigned_theme].name
    override = TITLE_OVERRIDES.get((book.volume, entry.scripture))
    if override:
        override_key = override.lower()
        if override_key in used:
            raise ValueError(f"Duplicate title override for {entry.scripture}: {override}")
        used.add(override_key)
        return override

    # Prefer language already earned by the page. The source drafts usually
    # open with a concise pastoral sentence that names the passage's actual
    # movement more faithfully than a reusable subject/suffix combination.
    sentence_candidates: list[tuple[int, str]] = []
    semantic_source = " ".join(
        [entry.original_title, entry.lens, entry.step, entry.prompt, entry.scripture_text]
    ).lower()
    semantic_tokens = {
        word
        for word in re.findall(r"[a-z']+", semantic_source)
        if len(word) > 4
    }
    for paragraph_index, paragraph in enumerate(entry.body[:3]):
        for sentence_index, sentence in enumerate(split_sentences(paragraph)):
            candidate = clean_sentence_text(sentence).strip(" \"'.,;:!?")
            if not candidate or re.search(r"\b\d+:\d+\b", candidate):
                continue
            if '"' in candidate:
                continue
            if re.match(
                r"^(?:And|But|Because|For|He|His|It|So|That|The disciples|These|They|This|Those|Yet|There)\b",
                candidate,
                flags=re.I,
            ):
                continue
            words = re.findall(r"[A-Za-z][A-Za-z'-]*", candidate)
            if not 5 <= len(words) <= 14:
                continue
            if re.search(
                r"\b(?:the Gospel writer|the passage|the reader|the reading|the Scripture|the text|the verse|this Scripture)\b",
                candidate,
                flags=re.I,
            ):
                continue
            if re.match(r"^(?:Practice|Respond to|Return to|Carry the truth|Let the reading)\b", candidate, flags=re.I):
                continue
            if re.search(r"\bthe heart is that\b", candidate, flags=re.I):
                continue
            title = headline_case(candidate)
            if title.lower() in used or not title_is_clean(title):
                continue
            content_words = {word.lower().rstrip("'s") for word in words if len(word) > 4}
            overlap = len(content_words.intersection(semantic_tokens))
            score = 100 - paragraph_index * 18 - sentence_index * 5
            score += overlap * 4
            if 6 <= len(words) <= 11:
                score += 12
            if re.search(r"\b(?:Father|God|Jesus|Christ|Spirit|love|mercy|grace|faith|hope|fear|heart)\b", title, flags=re.I):
                score += 7
            sentence_candidates.append((score, title))
    for _, title in sorted(sentence_candidates, key=lambda item: (item[0], item[1]), reverse=True):
        prefix = " ".join(re.findall(r"[a-z']+", title.lower())[:4])
        prefix_key = f"sentence-prefix:{prefix}"
        if subject_use[prefix_key] >= 9:
            continue
        subject_use[prefix_key] += 1
        used.add(title.lower())
        return title

    subjects = TITLE_SUBJECTS[book.volume]
    seed = int(hashlib.sha256(f"titles:{book.volume}:{entry.scripture}".encode()).hexdigest()[:12], 16)
    subject_candidates = list(subjects)
    if entry.day_number % 9 == 0:
        subject_candidates.insert(0, theme)
    title_stopwords = {
        "a", "an", "and", "at", "before", "by", "for", "from", "his", "in",
        "into", "is", "of", "on", "or", "the", "to", "when", "where", "with",
        "you", "your",
    }

    def semantic_words(text: str) -> list[str]:
        return [
            re.sub(r"'s$", "", word)
            for word in re.findall(r"[a-z']+", text.lower())
            if word not in title_stopwords
        ]

    semantic_signal = " ".join(
        [entry.original_title, entry.lens, *entry.body, entry.step, entry.prompt, entry.scripture_text, theme]
    )
    signal_counts = Counter(semantic_words(semantic_signal))
    original_counts = Counter(semantic_words(entry.original_title))
    signal_bigrams = set(zip(semantic_words(semantic_signal), semantic_words(semantic_signal)[1:]))

    ranked_candidates: list[tuple[int, int, int, int, str, str, str, str]] = []
    for subject in subject_candidates:
        subject_key = subject.lower()
        if subject_use[subject_key] >= 14 or subject_key in recent_subjects[-5:]:
            continue
        subject_words = re.findall(r"[a-z']+", subject.lower())
        subject_content = {re.sub(r"'s$", "", word) for word in subject_words} - title_stopwords
        subject_score = sum(signal_counts[word] * 2 + original_counts[word] * 7 for word in subject_content)
        subject_score += len(set(zip(semantic_words(subject), semantic_words(subject)[1:])).intersection(signal_bigrams)) * 9
        if subject.lower() in entry.original_title.lower():
            subject_score += 40
        if subject.lower() == theme.lower():
            subject_score += 12

        for suffix in NATURAL_TITLE_SUFFIXES:
            suffix_key = suffix.lower()
            if ending_use[suffix_key] >= 5 or suffix_key in recent_endings[-4:]:
                continue
            suffix_words = re.findall(r"[a-z']+", suffix.lower())
            suffix_content = {re.sub(r"'s$", "", word) for word in suffix_words} - title_stopwords
            if subject_content.intersection(suffix_content):
                continue
            title_connectors = {"for", "where", "with", "when", "before", "after"}
            if (set(subject_words) & title_connectors).intersection(set(suffix_words) & title_connectors):
                continue
            subject_bigrams = set(zip(subject_words, subject_words[1:]))
            suffix_bigrams = set(zip(suffix_words, suffix_words[1:]))
            if subject_bigrams.intersection(suffix_bigrams):
                continue
            if suffix_words and suffix_words[0] in subject_words[-3:]:
                continue
            title = headline_case(f"{subject} {suffix}")
            if not title_is_clean(title) or len(title.split()) > 14 or title.lower() in used:
                continue
            suffix_score = sum(signal_counts[word] for word in suffix_content)
            stable = int(hashlib.sha256(f"{seed}:{subject}:{suffix}".encode()).hexdigest()[:12], 16)
            ranked_candidates.append(
                (
                    subject_score * 10 + suffix_score * 3,
                    -subject_use[subject_key],
                    -ending_use[suffix_key],
                    stable,
                    title,
                    subject_key,
                    suffix_key,
                    suffix,
                )
            )

    # Semantic fit leads; usage balance and deterministic jitter break close ties.
    for _, _, _, _, title, subject_key, suffix_key, _ in sorted(ranked_candidates, reverse=True):
        used.add(title.lower())
        ending_use[suffix_key] += 1
        recent_endings.append(suffix_key)
        subject_use[subject_key] += 1
        recent_subjects.append(subject_key)
        return title
    raise ValueError(f"Unable to generate a unique title for {entry.scripture}")


def headline_case(text: str) -> str:
    small = {"a", "an", "and", "at", "by", "for", "from", "in", "of", "on", "or", "the", "to", "with"}
    words = text.split()
    result: list[str] = []
    for index, word in enumerate(words):
        bare = word.lower()
        follows_title_break = bool(result and result[-1].endswith((":", "-")))
        if index > 0 and bare in small and not follows_title_break:
            result.append(bare)
        else:
            result.append(word[:1].upper() + word[1:])
    return " ".join(result)


def revised_closing(book: Book, entry: Entry) -> str:
    patterns = CLOSING_PATTERNS[book.volume]
    seed = int(hashlib.sha256(f"closing:{entry.scripture}".encode()).hexdigest()[:8], 16)
    theme = book.themes[entry.assigned_theme].name.lower()
    base = patterns[seed % len(patterns)].format(theme=theme, image=verse_image(entry))
    base = base.rstrip(".").replace(". ", "; ")
    base = re.sub(
        r"receive\s+" + re.escape(theme),
        f"receive the truth of '{theme}'",
        base,
        flags=re.I,
    )
    base = re.sub(r"; ([A-Z])", lambda match: "; " + match.group(1).lower(), base)
    return f"Under the words '{entry.title},' {base[:1].lower() + base[1:]}."


def assign_connections(book: Book, entries: list[Entry], kjv: dict[str, str]) -> None:
    preferred_books = {
        1: {
            "Psalm", "Proverbs", "Isaiah", "Jeremiah", "Lamentations", "Hosea", "Micah",
            "Matthew", "Mark", "Luke", "John", "Romans", "Galatians", "Ephesians",
            "Philippians", "Colossians", "Hebrews", "James", "1 Peter", "1 John",
        },
        2: {
            "Psalm", "Proverbs", "Isaiah", "Jeremiah", "Micah", "Mark", "Luke", "John",
            "Acts", "Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
            "Philippians", "Colossians", "Hebrews", "James", "1 Peter", "2 Peter", "1 John",
        },
        3: {
            "Psalm", "Isaiah", "Ezekiel", "Joel", "Zechariah", "John", "Acts", "Romans",
            "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians", "Philippians",
            "1 Thessalonians", "2 Timothy", "Titus", "Hebrews", "James", "1 Peter",
            "2 Peter", "1 John", "Revelation",
        },
    }[book.volume]
    parsed_candidates: list[tuple[str, str, str, set[str]]] = []
    dissonant_words = {
        "adulteress", "harlot", "harlots", "rebellious", "thieves", "wicked", "wickedness",
        "slay", "slain", "kill", "killed", "wrath", "damnation", "curse", "cursed",
        "abomination", "abominations", "baal", "condemn", "condemnation", "death", "dead",
        "destruction", "enemy", "enemies", "judgment", "perish", "punish", "punished",
        "punishment", "scourge", "shame", "sword", "transgression", "transgressions", "unholy",
        "astray", "denied", "deny", "denying", "evil", "forsaken", "hate", "iniquity", "sinner",
        "sinners", "stumble", "stumbled",
    }
    for reference, verse_text in kjv.items():
        ref_book, _, _ = parse_reference(reference)
        words = verse_text.split()
        if ref_book not in preferred_books or not 6 <= len(words) <= 48:
            continue
        tokens = set(re.findall(r"[a-z]+", verse_text.lower()))
        if tokens.intersection(dissonant_words):
            continue
        parsed_candidates.append((reference, verse_text, ref_book, tokens))

    candidates_by_theme: list[list[tuple[str, str, str, set[str]]]] = []
    for theme in book.themes:
        candidates_by_theme.append(
            [
                candidate
                for candidate in parsed_candidates
                if any(any(token.startswith(keyword) for token in candidate[3]) for keyword in theme.keywords)
            ]
        )

    used: set[str] = set()
    book_use: Counter[str] = Counter()
    previous_book = ""
    for entry in entries:
        theme = book.themes[entry.assigned_theme]
        theme_keywords = set(theme.keywords)
        entry_keywords = {
            word.lower()
            for word in re.findall(r"[A-Za-z]+", " ".join([entry.core, entry.step, entry.prompt]))
            if len(word) > 4
        }
        ranked: list[tuple[int, int, str, str, str]] = []
        for reference, verse_text, ref_book, tokens in candidates_by_theme[entry.assigned_theme]:
            if reference in used or reference == entry.scripture or ref_book == entry.book:
                continue
            theme_overlap = sum(1 for keyword in theme_keywords if any(token.startswith(keyword) for token in tokens))
            entry_overlap = sum(1 for keyword in entry_keywords if any(token.startswith(keyword[:5]) for token in tokens))
            if theme_overlap == 0 and entry_overlap == 0:
                continue
            diversity = 18 if ref_book != previous_book else 0
            balance = max(0, 12 - book_use[ref_book])
            stable = int(hashlib.sha256(f"{entry.scripture}:{reference}".encode()).hexdigest()[:8], 16)
            ranked.append((entry_overlap * 45 + theme_overlap * 22 + diversity + balance, stable, reference, verse_text, ref_book))
        if not ranked:
            for reference, verse_text, ref_book, _ in parsed_candidates:
                if reference not in used and reference != entry.scripture and ref_book != entry.book:
                    stable = int(hashlib.sha256(f"fallback:{entry.scripture}:{reference}".encode()).hexdigest()[:8], 16)
                    ranked.append((0, stable, reference, verse_text, ref_book))
        selected = max(ranked, key=lambda row: (row[0], row[1]))
        entry.connection_reference = selected[2]
        entry.connection_text = selected[3]
        entry.connection_book = selected[4]
        used.add(entry.connection_reference)
        book_use[entry.connection_book] += 1
        previous_book = entry.connection_book


def finalize_entries(book: Book, entries: list[Entry], kjv: dict[str, str]) -> list[Entry]:
    if book.volume == 2:
        reassign_volume_2_scriptures(entries, kjv)
    assigned = assign_themes(book, entries)
    used_titles: set[str] = set()
    title_ending_use: Counter[str] = Counter()
    recent_title_endings: list[str] = []
    title_subject_use: Counter[str] = Counter()
    recent_title_subjects: list[str] = []
    used_closings: set[str] = set()
    used_body_sentences: set[str] = set()
    ordered: list[Entry] = []
    day_number = 0
    for theme_index, ((month, count), theme_entries) in enumerate(zip(MONTHS, assigned)):
        scheduled = schedule_theme(theme_entries, theme_index)
        if len(scheduled) != count:
            raise ValueError(f"{book.title} {month}: expected {count}, found {len(scheduled)}")
        for day_of_month, entry in enumerate(scheduled, start=1):
            day_number += 1
            entry.day_number = day_number
            entry.date_label = f"{month} {day_of_month}"
            entry.body = clean_body(book, entry)
            entry.body = remove_reused_body_sentences(entry.body, used_body_sentences)
            entry.context_label, entry.lens = clean_lens(book, entry)
            entry.step = clean_step(clean_journey_field(book, entry, entry.step))
            entry.prompt = clean_prompt(clean_journey_field(book, entry, entry.prompt))
            entry.prayer = clean_prayer(clean_journey_field(book, entry, entry.prayer))
            if not entry.step:
                entry.step = "Carry one truth from this Scripture into a concrete act of faith today."
            if not entry.prompt:
                entry.prompt = "What is this Scripture inviting me to trust or practice today?"
            if not entry.prayer:
                entry.prayer = {
                    1: "Father, let this Scripture lead me into honest trust and faithful love. Amen.",
                    2: "Jesus, keep me near Your voice and make my next step faithful. Amen.",
                    3: "Holy Spirit, form this Scripture into faithful fruit in my life. Amen.",
                }[book.volume]
            apply_passage_body_rewrites(book, entry)
            entry.title = revised_title(
                book,
                entry,
                used_titles,
                title_ending_use,
                recent_title_endings,
                title_subject_use,
                recent_title_subjects,
            )
            entry.closing = extract_reader_closing(entry, used_closings)
            deepen_entry(book, entry)
            apply_passage_body_rewrites(book, entry)
            ordered.append(entry)

    bonus = next(entry for entry in entries if entry.original_day == 59.5)
    bonus.assigned_theme = 1
    bonus.day_number = 0
    bonus.date_label = "February 29"
    bonus.title = "Grace for the Extra Day"
    bonus.body = clean_body(book, bonus)
    bonus.body = remove_reused_body_sentences(bonus.body, used_body_sentences)
    bonus.context_label, bonus.lens = clean_lens(book, bonus)
    bonus.step = clean_step(clean_journey_field(book, bonus, bonus.step))
    bonus.prompt = clean_prompt(clean_journey_field(book, bonus, bonus.prompt))
    bonus.prayer = clean_prayer(clean_journey_field(book, bonus, bonus.prayer))
    if not bonus.step:
        bonus.step = "Carry one truth from this Scripture into a concrete act of faith today."
    if not bonus.prompt:
        bonus.prompt = "What is this Scripture inviting me to trust or practice today?"
    if not bonus.prayer:
        bonus.prayer = {
            1: "Father, let this Scripture lead me into honest trust and faithful love. Amen.",
            2: "Jesus, keep me near Your voice and make my next step faithful. Amen.",
            3: "Holy Spirit, form this Scripture into faithful fruit in my life. Amen.",
        }[book.volume]
    apply_passage_body_rewrites(book, bonus)
    bonus.closing = extract_reader_closing(bonus, used_closings)
    deepen_entry(book, bonus)
    apply_passage_body_rewrites(book, bonus)
    ordered.insert(59, bonus)
    if ENABLE_AUTOMATIC_CONNECTIONS:
        assign_connections(book, ordered, kjv)
        for entry in ordered:
            entry.body.append(connection_reflection(book, entry))
    return ordered


def response_text(entry: Entry) -> str:
    if entry.step and entry.prompt:
        return f"{entry.step} Then sit with this question: {entry.prompt}"
    return entry.step or entry.prompt


def front_matter(book: Book) -> str:
    return f"""# {book.title}

## {book.subtitle}

{AUTHOR}

Revised Reader Edition

## A Welcome from Lady D

Dear reader,

Bring your real morning to these pages. Bring the questions that followed you into the night, the responsibilities already calling your name, and the places where your faith feels strong or tired. You do not have to perform here. Begin with Scripture. Let God speak before fear, pressure, or another person's opinion gets the first word.

Read slowly enough to notice what meets your life. Pray honestly. Write what is true. Then take one faithful response into the day. My prayer is that this journey helps you know God's love more deeply, walk with Jesus more closely, and make room for the Holy Spirit to form a life that is both tender and strong.

With love,

Lady D

## How to Use This Book

1. Read the full KJV Scripture printed at the beginning of the day.
2. Receive the devotional as a conversation, not an assignment to perform.
3. Use the short context note only to clarify the verse; return to the Scripture itself as the authority.
4. Pray the written prayer aloud or make it your own.
5. Complete the fused reflection-and-response prompt in the companion journal.

## Scripture Note

Scripture quotations in this reader edition are from the King James Version (KJV), using the standardized 1769 text distributed by eBible.org. Each daily passage is printed in full so the devotional begins in the Word itself. The reflections are pastoral applications and should always be read under the authority of the biblical text.

The February 29 reading is bonus material for leap years or any day when the reader needs an extra place to pause. Dates are shown without weekdays so the devotional can be used in any year. Sabbath is treated as the seventh-day Sabbath where the biblical passage or theme calls for it.
"""


def manuscript_markdown(book: Book, entries: list[Entry]) -> str:
    pieces = [front_matter(book)]
    month_entries: dict[str, list[Entry]] = defaultdict(list)
    for entry in entries:
        month_entries[entry.date_label.split()[0]].append(entry)
    for index, (month, _) in enumerate(MONTHS):
        theme = book.themes[index]
        pieces.extend(
            [
                "",
                "---",
                "",
                f"# {month}: {theme.name}",
                "",
                theme.promise,
                "",
            ]
        )
        for entry in month_entries[month]:
            bonus = entry.day_number == 0
            day_meta = "Bonus Reading" if bonus else f"Day {entry.day_number:03d}"
            pieces.extend(
                [
                    "---",
                    "",
                    f"## {entry.date_label} | {day_meta}",
                    "",
                    f"### {entry.title}",
                    "",
                    f"**Scripture: {entry.scripture} (KJV)**",
                    "",
                    f"> {entry.scripture_text}",
                    "",
                ]
            )
            if entry.lens:
                pieces.extend([f"**{entry.context_label}:** {entry.lens}", ""])
            if entry.connection_text:
                pieces.extend(
                    [
                        f"**Scripture connection: {entry.connection_reference} (KJV)**",
                        "",
                        f"> {entry.connection_text}",
                        "",
                    ]
                )
            pieces.extend(entry.body)
            pieces.extend(
                [
                    "",
                    entry.closing,
                    "",
                    f"**Prayer:** {entry.prayer}",
                    "",
                    f"**Reflect and respond:** {response_text(entry)}",
                    "",
                ]
            )
    pieces.extend(["---", "", "# Scripture Journey Index", "", "References are listed in biblical order. Final print page numbers are added by the paginated interior builder.", ""])
    index_rows = sorted(entries, key=lambda entry: (BOOK_ORDER.get(entry.book, 999), entry.chapter, entry.verse))
    pieces.extend(["| Scripture | Reading date | Day | Title |", "| --- | --- | ---: | --- |"])
    for entry in index_rows:
        day = "Bonus" if entry.day_number == 0 else str(entry.day_number)
        pieces.append(f"| {entry.scripture} | {entry.date_label} | {day} | {entry.title} |")
    return "\n".join(pieces)


JOURNAL_PRAYER_RECORD_PROMPTS = (
    "What do I need to tell God honestly, and what am I placing in His hands?",
    "What am I grateful for, and what burden am I releasing to God?",
    "Where do I need God's help, and what truth will I pray back to Him?",
    "What is difficult to admit, and how will I bring it into God's presence?",
    "What promise do I need to receive, and what fear do I need to surrender?",
    "Who needs prayer today, and what will I ask God to do in me?",
    "What emotion needs honest prayer, and where am I asking for peace?",
    "What have I heard from Scripture, and how will I answer God?",
    "Where do I need forgiveness, courage, or wisdom from God?",
    "What unfinished concern will I name before God instead of carrying it alone?",
    "What act of mercy am I asking God to form in me?",
    "What do I want to remember about God's presence in this reading?",
)

JOURNAL_FOLLOW_THROUGH_PROMPTS = (
    "What will I revisit before this day closes?",
    "What one response will I complete before the day ends?",
    "Where will I pause and remember this Scripture again?",
    "Whom will I contact, encourage, forgive, or serve?",
    "What choice will show that I received today's truth?",
    "What will I stop, start, or continue because of this reading?",
    "What reminder will help me carry this prayer into the day?",
    "Where will I practice this truth in ordinary life?",
    "What conversation or task needs this Scripture's guidance?",
    "What will I return to in prayer tonight?",
    "How will I notice whether my response became action?",
    "What grace from today do I want to carry into tomorrow?",
)


def journal_ritual_prompts(entry: Entry) -> tuple[str, str]:
    seed = entry.day_number if entry.day_number else int(entry.original_day * 10)
    return (
        JOURNAL_PRAYER_RECORD_PROMPTS[seed % len(JOURNAL_PRAYER_RECORD_PROMPTS)],
        JOURNAL_FOLLOW_THROUGH_PROMPTS[(seed * 5 + 3) % len(JOURNAL_FOLLOW_THROUGH_PROMPTS)],
    )


def journal_markdown(book: Book, entries: list[Entry]) -> str:
    pieces = [
        f"# {book.title}: Companion Journal",
        "",
        f"## A guided journal for {book.subtitle.lower()}",
        "",
        AUTHOR,
        "",
        "Use this journal beside the devotional. Return to the printed Scripture, tell the truth before God, and leave each page with one clear response. The prompts are intentionally direct so the journal supports the devotion rather than repeating it.",
        "",
    ]
    month_entries: dict[str, list[Entry]] = defaultdict(list)
    for entry in entries:
        month_entries[entry.date_label.split()[0]].append(entry)
    for index, (month, _) in enumerate(MONTHS):
        theme = book.themes[index]
        pieces.extend(["---", "", f"# {month}: {theme.name}", "", theme.promise, ""])
        for entry in month_entries[month]:
            prayer_record, follow_through = journal_ritual_prompts(entry)
            day_meta = "Bonus Reading" if entry.day_number == 0 else f"Day {entry.day_number:03d}"
            pieces.extend(
                [
                    f"## {entry.date_label} | {day_meta}",
                    "",
                    f"### {entry.title}",
                    "",
                    f"**Return to the Word:** {entry.scripture} (KJV)",
                    "",
                    f"> {entry.scripture_text}",
                    "",
                    f"**Observe:** What word, action, promise, warning, or picture stands out in {entry.scripture}?",
                    "",
                    f"**Reflect:** {entry.prompt}",
                    "",
                    f"**Act:** {entry.step}",
                    "",
                    f"**Prayer starter:** {entry.prayer}",
                    "",
                    f"**Prayer record:** {prayer_record}",
                    "",
                    f"**Follow-through:** {follow_through}",
                    "",
                    "**Write:**",
                    "",
                    *(line for _ in range(9) for line in ("____________________________________________________________________________", "")),
                ]
            )
        pieces.extend(
            [
                f"## {month} Review",
                "",
                f"Where did {theme.name.lower()} become real in my life this month?",
                "",
                "What truth do I want to carry forward?",
                "",
                "What is my next faithful response?",
                "",
            ]
        )
    return "\n".join(pieces)


def entry_payload(entry: Entry) -> dict[str, object]:
    prayer_record, follow_through = journal_ritual_prompts(entry)
    return {
        "day_number": entry.day_number,
        "date": entry.date_label,
        "title": entry.title,
        "scripture_reference": entry.scripture,
        "scripture_translation": "KJV",
        "scripture_text": entry.scripture_text,
        "scripture_connection_reference": entry.connection_reference,
        "scripture_connection_text": entry.connection_text,
        "context_label": entry.context_label,
        "context": entry.lens,
        "body": entry.body,
        "closing": entry.closing,
        "prayer": entry.prayer,
        "reflection_and_response": response_text(entry),
        "journal_observe": f"What word, action, promise, warning, or picture stands out in {entry.scripture}?",
        "journal_reflect": entry.prompt,
        "journal_act": entry.step,
        "journal_prayer_record": prayer_record,
        "journal_follow_through": follow_through,
        "source_provenance": {
            "original_day": entry.original_day,
            "original_date": entry.original_date,
            "original_title": entry.original_title,
            "original_scripture": entry.source_scripture,
            "source_heading": entry.source_heading,
        },
    }


def audit_book(book: Book, entries: list[Entry]) -> dict[str, object]:
    titles = [entry.title.lower() for entry in entries]
    refs = [entry.scripture for entry in entries]
    connection_refs = [entry.connection_reference for entry in entries if entry.connection_reference]
    body_words = [len(" ".join(entry.body).split()) for entry in entries]
    adjacent_same_book = sum(1 for left, right in zip(entries, entries[1:]) if left.book == right.book)
    adjacent_same_chapter = sum(
        1
        for left, right in zip(entries, entries[1:])
        if left.book == right.book and left.chapter == right.chapter
    )
    adjacent_same_connection_book = sum(
        1
        for left, right in zip(entries, entries[1:])
        if left.connection_book and right.connection_book and left.connection_book == right.connection_book
    )
    all_text = "\n".join(
        " ".join([entry.title, entry.lens, *entry.body, entry.closing, entry.prayer, response_text(entry)])
        for entry in entries
    ).lower()
    banned_counts = {fragment: all_text.count(fragment) for fragment in BANNED_SENTENCE_FRAGMENTS}
    return {
        "volume": book.volume,
        "title": book.title,
        "entries": len(entries),
        "dated_entries": sum(1 for entry in entries if entry.day_number > 0),
        "bonus_entries": sum(1 for entry in entries if entry.day_number == 0),
        "visible_scripture_texts": sum(bool(entry.scripture_text) for entry in entries),
        "visible_scripture_connections": sum(bool(entry.connection_text) for entry in entries),
        "prayers": sum(bool(entry.prayer) for entry in entries),
        "reflection_and_response": sum(bool(response_text(entry)) for entry in entries),
        "unique_titles": len(set(titles)),
        "duplicate_titles": [title for title, count in Counter(titles).items() if count > 1],
        "unique_scripture_references": len(set(refs)),
        "duplicate_scripture_references": [ref for ref, count in Counter(refs).items() if count > 1],
        "unique_scripture_connections": len(set(connection_refs)),
        "duplicate_scripture_connections": [ref for ref, count in Counter(connection_refs).items() if count > 1],
        "body_words": {
            "minimum": min(body_words),
            "maximum": max(body_words),
            "average": round(sum(body_words) / len(body_words), 1),
        },
        "adjacent_same_book": adjacent_same_book,
        "adjacent_same_chapter": adjacent_same_chapter,
        "adjacent_same_connection_book": adjacent_same_connection_book,
        "calendar_specific_sabbath_artifacts": len(re.findall(r"2026 production calendar|falls on saturday|falls on the seventh-day sabbath", all_text)),
        "old_today_step_labels": all_text.count("today step"),
        "old_morning_impact_labels": all_text.count("morning impact"),
        "banned_phrase_counts": banned_counts,
        "month_counts": {
            month: sum(1 for entry in entries if entry.date_label.startswith(month))
            for month, _ in MONTHS
        },
        "book_distribution": dict(sorted(Counter(entry.book for entry in entries).items(), key=lambda item: BOOK_ORDER.get(item[0], 999))),
        "connection_book_distribution": dict(sorted(Counter(entry.connection_book for entry in entries if entry.connection_book).items(), key=lambda item: BOOK_ORDER.get(item[0], 999))),
    }


def volume_html(book: Book, entries: list[Entry]) -> str:
    month_nav = "".join(
        f'<a href="#month-{index + 1}">{html.escape(month)}</a>' for index, (month, _) in enumerate(MONTHS)
    )
    by_month: dict[str, list[Entry]] = defaultdict(list)
    for entry in entries:
        by_month[entry.date_label.split()[0]].append(entry)
    sections: list[str] = []
    for index, (month, _) in enumerate(MONTHS):
        theme = book.themes[index]
        cards = []
        for entry in by_month[month]:
            cards.append(
                f"""<article class="entry" id="day-{entry.day_number if entry.day_number else 'bonus'}">
  <p class="date">{html.escape(entry.date_label)} {'/ Bonus Reading' if entry.day_number == 0 else f'/ Day {entry.day_number:03d}'}</p>
  <h3>{html.escape(entry.title)}</h3>
  <p class="reference">{html.escape(entry.scripture)} / KJV</p>
  <blockquote>{html.escape(entry.scripture_text)}</blockquote>
  {f'<p class="context"><strong>{html.escape(entry.context_label)}:</strong> {html.escape(entry.lens)}</p>' if entry.lens else ''}
  {f'<p class="connection"><strong>Scripture connection: {html.escape(entry.connection_reference)} / KJV</strong><br>{html.escape(entry.connection_text)}</p>' if entry.connection_text else ''}
  {''.join(f'<p>{html.escape(paragraph)}</p>' for paragraph in entry.body)}
  <p class="closing">{html.escape(entry.closing)}</p>
  <p class="prayer"><strong>Prayer:</strong> {html.escape(entry.prayer)}</p>
  <p class="response"><strong>Reflect and respond:</strong> {html.escape(response_text(entry))}</p>
</article>"""
            )
        sections.append(
            f"""<section class="month" id="month-{index + 1}">
  <div class="month-head"><p>{html.escape(month)}</p><h2>{html.escape(theme.name)}</h2><span>{html.escape(theme.promise)}</span></div>
  <div class="entry-list">{''.join(cards)}</div>
</section>"""
        )
    slug = f"volume-{book.volume}"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(book.title)} Reader Edition | Lady D</title>
  <style>
    :root{{--paper:#fbfaf7;--ink:#17191c;--muted:#666b73;--line:#d9d6cf;--accent:{book.accent};--soft:#f1eee7}}
    *{{box-sizing:border-box}} html{{scroll-behavior:smooth}} body{{margin:0;background:var(--paper);color:var(--ink);font-family:Arial,sans-serif;line-height:1.58}}
    nav{{position:sticky;top:0;z-index:5;display:flex;gap:8px;overflow:auto;padding:10px 16px;background:#151719;border-bottom:1px solid #333}}
    nav a{{color:#fff;text-decoration:none;white-space:nowrap;font-size:12px;font-weight:700;padding:7px 9px}}
    header{{padding:48px max(20px,calc((100vw - 920px)/2));border-bottom:1px solid var(--line)}}
    .kicker,.date,.month-head p{{margin:0 0 8px;color:var(--accent);font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:0}}
    h1,h2,h3{{font-family:Georgia,serif;letter-spacing:0;line-height:1.08}} h1{{max-width:800px;font-size:clamp(40px,7vw,76px);margin:0 0 12px}} h2{{font-size:32px;margin:0 0 7px}} h3{{font-size:25px;margin:0 0 8px}}
    header p{{max-width:720px;font-size:18px;color:var(--muted)}} .downloads{{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}} .downloads a{{color:#fff;background:var(--accent);text-decoration:none;padding:10px 13px;font-size:13px;font-weight:800;border-radius:4px}}
    main{{max-width:920px;margin:auto;padding:0 20px 80px}} .month{{padding-top:54px}} .month-head{{padding:0 0 20px;border-bottom:3px solid var(--accent)}} .month-head span{{color:var(--muted)}}
    .entry{{padding:38px 0;border-bottom:1px solid var(--line)}} .reference{{font-weight:800;color:var(--accent)}} blockquote{{margin:18px 0;padding:18px 20px;border-left:4px solid var(--accent);background:var(--soft);font-family:Georgia,serif;font-size:17px}}
    .context{{padding:13px 15px;background:#f4f3ef;border:1px solid var(--line);font-size:14px}} .connection{{padding:13px 15px;border-left:3px solid var(--accent);background:#fff;font-size:14px}} .closing{{font-weight:800;font-family:Georgia,serif;font-size:17px}} .prayer,.response{{padding:14px 16px;border-left:3px solid var(--accent);background:#fff}}
    @media(max-width:620px){{header{{padding:34px 20px}} main{{padding-left:16px;padding-right:16px}} .entry{{padding:30px 0}} h3{{font-size:22px}} blockquote{{margin-left:0;margin-right:0}}}}
    @media print{{nav,.downloads{{display:none}} header{{padding:0 0 24px}} .entry{{break-before:page;border:0}} body{{background:#fff}}}}
  </style>
</head>
<body>
  <nav><a href="lady-d-revised-trilogy.html">Trilogy</a>{month_nav}</nav>
  <header><p class="kicker">Volume {book.volume} / Revised Reader Edition</p><h1>{html.escape(book.title)}</h1><p>{html.escape(book.subtitle)} by {html.escape(AUTHOR)}. Visible KJV Scripture, stronger devotional movement, and one clear reflection-and-response ending.</p>
    <div class="downloads"><a href="downloads/production/revised-reader-edition/{slug}/{slug}-reader-edition.md">Manuscript</a><a href="downloads/production/revised-reader-edition/{slug}/{slug}-companion-journal.md">Companion Journal</a><a href="downloads/production/revised-reader-edition/{slug}/{slug}-reader-edition.json">Structured Data</a></div>
  </header>
  <main>{''.join(sections)}</main>
</body>
</html>"""


def trilogy_html(payloads: list[tuple[Book, list[Entry], dict[str, object]]]) -> str:
    books_html = []
    for book, entries, audit in payloads:
        sample = entries[0]
        books_html.append(
            f"""<article class="book">
  <img src="{html.escape(book.cover)}" alt="{html.escape(book.title)} cover concept">
  <div><p class="eyebrow">Volume {book.volume} / {html.escape(book.lane)}</p><h2>{html.escape(book.title)}</h2><p>{html.escape(book.subtitle)}</p>
  <dl><div><dt>Readings</dt><dd>{audit['entries']}</dd></div><div><dt>Scripture Texts</dt><dd>{audit['visible_scripture_texts'] + audit['visible_scripture_connections']}</dd></div><div><dt>Unique Titles</dt><dd>{audit['unique_titles']}</dd></div></dl>
  <p class="sample"><strong>{html.escape(sample.date_label)}:</strong> {html.escape(sample.title)} / {html.escape(sample.scripture)}</p>
  <div class="actions"><a href="volume-{book.volume}-revised-reader-edition.html">Open full reader edition</a><a href="downloads/production/revised-reader-edition/volume-{book.volume}/volume-{book.volume}-reader-edition.md">Download manuscript</a><a href="downloads/production/revised-reader-edition/volume-{book.volume}/volume-{book.volume}-companion-journal.md">Download journal</a></div></div>
</article>"""
        )
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Lady D Revised Trilogy</title>
<style>
:root{{--paper:#f8f7f3;--ink:#17191d;--muted:#656a72;--line:#d7d4cd;--gold:#8b6635}}*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font-family:Arial,sans-serif;line-height:1.55}}nav{{display:flex;gap:12px;padding:13px 20px;background:#17191d;overflow:auto}}nav a{{color:#fff;text-decoration:none;white-space:nowrap;font-size:13px;font-weight:800}}header,main{{max-width:1120px;margin:auto;padding:44px 22px}}header{{border-bottom:1px solid var(--line)}}.eyebrow{{color:var(--gold);font-size:12px;font-weight:900;text-transform:uppercase;letter-spacing:0}}h1,h2{{font-family:Georgia,serif;letter-spacing:0;line-height:1.05}}h1{{font-size:clamp(42px,7vw,82px);max-width:900px;margin:0 0 14px}}header>p{{max-width:780px;color:var(--muted);font-size:19px}}.book{{display:grid;grid-template-columns:230px 1fr;gap:28px;padding:34px 0;border-bottom:1px solid var(--line)}}.book img{{width:100%;aspect-ratio:2/3;object-fit:cover;box-shadow:0 14px 34px #0002}}h2{{font-size:34px;margin:0 0 8px}}dl{{display:flex;gap:22px;flex-wrap:wrap;margin:22px 0}}dl div{{border-left:3px solid var(--gold);padding-left:10px}}dt{{font-size:11px;text-transform:uppercase;font-weight:800;color:var(--muted)}}dd{{margin:2px 0 0;font-family:Georgia,serif;font-size:25px}}.sample{{padding:14px;background:#fff;border:1px solid var(--line)}}.actions{{display:flex;gap:9px;flex-wrap:wrap}}.actions a{{background:#22262a;color:white;text-decoration:none;padding:10px 12px;border-radius:4px;font-size:13px;font-weight:800}}.truth{{margin-top:35px;padding:20px;border:1px solid var(--line);background:#fff}}@media(max-width:700px){{.book{{grid-template-columns:1fr}}.book img{{width:min(64vw,260px)}}header,main{{padding-left:18px;padding-right:18px}}}}
</style></head>
<body><nav><a href="susan-damon-hub.html">Lady D Hub</a><a href="production.html">Production</a><a href="release-status.html">Release Status</a><a href="#books">Revised Books</a></nav>
<header><p class="eyebrow">Transcript-directed manuscript correction</p><h1>The actual books have entered the Reader Edition.</h1><p>All three devotionals and all three companion journals now use the July 6 content contract: visible Scripture, fuller devotional movement, a warmer and more direct voice, thematic rather than mechanical sequencing, and one clear daily response.</p></header>
<main id="books">{''.join(books_html)}<section class="truth"><h2>Quality boundary</h2><p>This is the complete revised reader edition and the source for independent judge and auditor review. Final KDP release still requires author approval, final theological and copy proof, locked pagination, KDP Previewer, and a physical proof.</p><p><a href="downloads/production/revised-reader-edition/lady-d-reader-edition-audit.md">Open the machine audit</a></p></section></main></body></html>"""


def audit_markdown(audits: list[dict[str, object]]) -> str:
    lines = [
        "# Lady D Reader Edition Build Audit",
        "",
        f"Generated: {GENERATED}",
        "",
        "Status: Builder pass. Independent judge and auditor verdicts are separate release gates.",
        "",
        "## Transcript-Directed Contract",
        "",
        "- Full KJV Scripture text appears on every devotional and journal reading.",
        "- Today Step and Morning Impact are removed as separate labels.",
        "- Practical action and the journal question are fused under Reflect and respond.",
        "- Context language is retained only as a concise Word and context or Scripture context note.",
        "- Year-specific Saturday/Sabbath statements are removed so dates remain reusable.",
        "- Readings are reassigned to twelve thematic journeys and scheduled to reduce adjacent book/chapter clustering.",
        "- A biblical-order Scripture journey index is included in every devotional.",
        "",
    ]
    for audit in audits:
        lines.extend(
            [
                f"## Volume {audit['volume']}: {audit['title']}",
                "",
                f"- Entries: {audit['entries']} ({audit['dated_entries']} dated + {audit['bonus_entries']} bonus)",
                f"- Visible Scripture texts: {audit['visible_scripture_texts']}",
                f"- Visible paired Scripture connections: {audit['visible_scripture_connections']}",
                f"- Prayers: {audit['prayers']}",
                f"- Reflection and response endings: {audit['reflection_and_response']}",
                f"- Unique titles: {audit['unique_titles']}",
                f"- Unique primary Scripture references: {audit['unique_scripture_references']}",
                f"- Unique paired Scripture connections: {audit['unique_scripture_connections']}",
                f"- Body words: min {audit['body_words']['minimum']}, average {audit['body_words']['average']}, max {audit['body_words']['maximum']}",
                f"- Adjacent same-book readings: {audit['adjacent_same_book']}",
                f"- Adjacent same-chapter readings: {audit['adjacent_same_chapter']}",
                f"- Adjacent same-book Scripture connections: {audit['adjacent_same_connection_book']}",
                f"- Calendar-specific Sabbath artifacts: {audit['calendar_specific_sabbath_artifacts']}",
                f"- Old Today Step labels: {audit['old_today_step_labels']}",
                f"- Old Morning Impact labels: {audit['old_morning_impact_labels']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Release Gate",
            "",
            "The builder may only pass structure. The editorial judge must score the books for warmth, spiritual impact, clarity, faithfulness, and reader trust. The independent auditor must verify all 1,098 entries, journals, Scripture text, dates, repetition, and internal-language exclusions. Any severe finding returns the affected entries to remediation before KDP packaging.",
            "",
        ]
    )
    return "\n".join(lines)


def sync_tree(source: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)


def main() -> None:
    kjv = load_kjv()
    payloads: list[tuple[Book, list[Entry], dict[str, object]]] = []
    audits: list[dict[str, object]] = []
    OUT.mkdir(parents=True, exist_ok=True)
    for book in BOOKS:
        entries = finalize_entries(book, parse_master(book, kjv), kjv)
        volume_out = OUT / f"volume-{book.volume}"
        volume_out.mkdir(parents=True, exist_ok=True)
        write(volume_out / f"volume-{book.volume}-reader-edition.md", manuscript_markdown(book, entries))
        write(volume_out / f"volume-{book.volume}-companion-journal.md", journal_markdown(book, entries))
        payload = {
            "generated": GENERATED,
            "edition": "transcript-directed-reader-edition",
            "book": {
                "volume": book.volume,
                "title": book.title,
                "subtitle": book.subtitle,
                "author": AUTHOR,
                "lane": book.lane,
            },
            "themes": [asdict(theme) for theme in book.themes],
            "entries": [entry_payload(entry) for entry in entries],
        }
        write(volume_out / f"volume-{book.volume}-reader-edition.json", json.dumps(payload, indent=2, ensure_ascii=False))
        audit = audit_book(book, entries)
        write(volume_out / f"volume-{book.volume}-reader-edition-audit.json", json.dumps(audit, indent=2))
        page = volume_html(book, entries)
        write(ROOT / f"volume-{book.volume}-revised-reader-edition.html", page)
        write(ROOT / "public" / f"volume-{book.volume}-revised-reader-edition.html", page)
        audits.append(audit)
        payloads.append((book, entries, audit))

    combined = {
        "generated": GENERATED,
        "edition": "transcript-directed-reader-edition",
        "scripture_source": {
            "translation": "KJV",
            "source": "https://ebible.org/Scriptures/eng-kjv2006_usfm.zip",
            "sha256": checksum(KJV_ZIP),
        },
        "totals": {
            "devotional_entries": sum(audit["entries"] for audit in audits),
            "dated_entries": sum(audit["dated_entries"] for audit in audits),
            "bonus_entries": sum(audit["bonus_entries"] for audit in audits),
            "visible_scripture_texts": sum(audit["visible_scripture_texts"] for audit in audits),
            "visible_scripture_connections": sum(audit["visible_scripture_connections"] for audit in audits),
        },
        "volumes": audits,
    }
    write(OUT / "lady-d-reader-edition-audit.json", json.dumps(combined, indent=2))
    write(OUT / "lady-d-reader-edition-audit.md", audit_markdown(audits))
    trilogy_page = trilogy_html(payloads)
    write(ROOT / "lady-d-revised-trilogy.html", trilogy_page)
    write(ROOT / "public" / "lady-d-revised-trilogy.html", trilogy_page)
    sync_tree(OUT, PUBLIC_OUT)
    print(json.dumps(combined, indent=2))


if __name__ == "__main__":
    main()
