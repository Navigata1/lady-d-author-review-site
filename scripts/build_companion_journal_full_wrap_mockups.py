#!/usr/bin/env python3
"""Build preliminary full-wrap cover mockups for the companion journals."""

from __future__ import annotations

import shutil
import sys
import textwrap
import zipfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_full_wrap_cover_mockups import (  # noqa: E402
    BLEED,
    DPI,
    TRIM_H,
    TRIM_W,
    WHITE_SPINE_FACTOR,
    add_vertical_gradient,
    draw_centered_wrapped,
    draw_left_wrapped,
    fit_art,
    font,
    rect_inches,
)


OUTPUT = ROOT / "downloads" / "production" / "kdp" / "companion-journal-full-wrap-drafts"
PUBLIC_OUTPUT = ROOT / "public" / "downloads" / "production" / "kdp" / "companion-journal-full-wrap-drafts"
SOURCE_ASSETS = ROOT / "production-assets" / "companion-journal-full-wrap-drafts"
PUBLIC_ASSETS = ROOT / "public" / "production-assets" / "companion-journal-full-wrap-drafts"
PRODUCTION_LIBRARY = Path("/Users/IDC2.5/Documents/LADY D/Production Library")


@dataclass(frozen=True)
class JournalCover:
    volume: int
    title: str
    subtitle: str
    spine_title: str
    pages: int
    art: Path
    library_dir: str
    palette: tuple[str, str, str]
    blurb: str

    @property
    def spine(self) -> float:
        return self.pages * WHITE_SPINE_FACTOR

    @property
    def cover_width(self) -> float:
        return 12.25 + self.spine


JOURNALS = [
    JournalCover(
        volume=1,
        title="Surrendering to God's Love",
        subtitle="Companion Journal",
        spine_title="Surrendering to God's Love Journal",
        pages=470,
        art=ROOT / "production-assets" / "cover-02-path-of-surrender-art.png",
        library_dir="01 Surrendering to God's Love",
        palette=("#172447", "#f8efd7", "#d6a64a"),
        blurb=(
            "A guided companion journal for receiving the Father's heart one morning "
            "at a time. Includes daily response space, Sabbath reflections, weekly "
            "prayers, review pages, and a February 29 bonus reflection."
        ),
    ),
    JournalCover(
        volume=2,
        title="Walking with Jesus",
        subtitle="Companion Journal",
        spine_title="Walking with Jesus Journal",
        pages=477,
        art=ROOT / "production-assets" / "volume-2-cover-02-path-of-surrender-art.png",
        library_dir="02 Walking with Jesus",
        palette=("#13223f", "#fbf3dc", "#d1a044"),
        blurb=(
            "A year of written response beside the devotional journey with Jesus. "
            "These pages give the reader space to listen, follow, surrender, and "
            "practice grace-shaped obedience in ordinary life."
        ),
    ),
    JournalCover(
        volume=3,
        title="Filled with the Holy Spirit",
        subtitle="Companion Journal",
        spine_title="Filled with the Holy Spirit Journal",
        pages=483,
        art=ROOT / "production-assets" / "volume-3-cover-02-path-of-surrender-art.png",
        library_dir="03 Filled with the Holy Spirit",
        palette=("#0d343c", "#f7f0db", "#e0a63c"),
        blurb=(
            "A companion journal for Spirit-filled surrender: daily reflection pages, "
            "Sabbath response space, weekly prayers, review pages, and room to trace "
            "the fruit God is forming over a full year."
        ),
    ),
]


def draw_spine(canvas: Image.Image, journal: JournalCover, x0: int, y0: int, w: int, h: int) -> None:
    spine_layer = Image.new("RGBA", (h, w), (0, 0, 0, 0))
    d = ImageDraw.Draw(spine_layer)
    title_font = font(max(28, min(45, int(w * 0.48))), bold=True)
    author_font = font(max(19, min(28, int(w * 0.30))))
    cream = journal.palette[1]
    gold = journal.palette[2]
    d.text((round(h * 0.08), round(w * 0.19)), journal.spine_title.upper(), font=title_font, fill=cream)
    d.text((round(h * 0.72), round(w * 0.19)), "SUSAN \"LADY D\" DAMON", font=author_font, fill=gold)
    rotated = spine_layer.rotate(90, expand=True)
    canvas.alpha_composite(rotated.crop((0, 0, w, h)), (x0, y0))


def build_cover(journal: JournalCover) -> dict[str, str | int | float]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    width_px = round(journal.cover_width * DPI)
    height_px = round((TRIM_H + 2 * BLEED) * DPI)
    trim_px = round(TRIM_W * DPI)
    bleed_px = round(BLEED * DPI)
    spine_px = round(journal.spine * DPI)
    back_w = bleed_px + trim_px
    spine_x = back_w
    front_x = back_w + spine_px
    front_w = trim_px + bleed_px

    dark, cream, gold = journal.palette
    canvas = Image.new("RGBA", (width_px, height_px), dark)

    art_front = fit_art(journal.art, (front_w, height_px)).convert("RGBA")
    add_vertical_gradient(art_front, top_alpha=158, bottom_alpha=204)
    canvas.alpha_composite(art_front, (front_x, 0))

    art_back = ImageOps.fit(Image.open(journal.art).convert("RGB"), (back_w, height_px), method=Image.Resampling.LANCZOS).convert("RGBA")
    art_back = art_back.filter(ImageFilter.GaussianBlur(18))
    art_back = ImageEnhance.Brightness(art_back).enhance(0.42)
    art_back = ImageEnhance.Color(art_back).enhance(0.5)
    canvas.alpha_composite(art_back, (0, 0))

    d = ImageDraw.Draw(canvas)
    d.rectangle((spine_x, 0, spine_x + spine_px, height_px), fill=dark)
    d.line((spine_x, 0, spine_x, height_px), fill=gold, width=max(2, round(DPI * 0.008)))
    d.line((spine_x + spine_px, 0, spine_x + spine_px, height_px), fill=gold, width=max(2, round(DPI * 0.008)))

    guide = (255, 255, 255, 52)
    d.rectangle(rect_inches(BLEED, BLEED, TRIM_W, TRIM_H), outline=guide, width=2)
    d.rectangle((front_x, bleed_px, front_x + trim_px, bleed_px + trim_px + round(3 * DPI)), outline=guide, width=2)

    text_x0 = front_x + round(0.5 * DPI)
    text_x1 = front_x + trim_px - round(0.5 * DPI)
    y = round(0.78 * DPI)
    d.text((text_x0, y), f"VOLUME {journal.volume} JOURNAL", font=font(32, bold=True), fill=gold)
    y += round(0.45 * DPI)
    y = draw_centered_wrapped(
        d,
        journal.title,
        (text_x0, y, text_x1, height_px),
        font(86, bold=True),
        cream,
        max_chars=18,
        line_gap=12,
    )
    y += round(0.2 * DPI)
    draw_centered_wrapped(d, journal.subtitle, (text_x0, y, text_x1, height_px), font(42, bold=True), cream, max_chars=22, line_gap=8)
    y += round(0.82 * DPI)
    draw_centered_wrapped(
        d,
        "Daily response pages, Sabbath reflections, weekly prayers, and review pages",
        (text_x0, y, text_x1, height_px),
        font(27),
        cream,
        max_chars=34,
        line_gap=8,
    )
    author_y = height_px - round(0.95 * DPI)
    draw_centered_wrapped(d, 'Susan "Lady D" Damon', (text_x0, author_y, text_x1, height_px), font(37, bold=True), cream, max_chars=30)

    back_x = round(0.62 * DPI)
    back_y = round(0.82 * DPI)
    d.text((back_x, back_y), "LADY D DEVOTIONAL LIBRARY", font=font(32, bold=True), fill=gold)
    back_y += round(0.65 * DPI)
    d.text((back_x, back_y), f"Volume {journal.volume} Companion Journal", font=font(45, bold=True), fill=cream)
    back_y += round(0.58 * DPI)
    back_y = draw_left_wrapped(d, journal.blurb, (back_x, back_y), trim_px, font(33), cream, max_chars=36, line_gap=10)
    back_y += round(0.38 * DPI)
    d.text((back_x, back_y), "Built from the current 6 x 9 journal draft page count.", font=font(27), fill=cream)
    back_y += round(0.47 * DPI)
    d.text((back_x, back_y), "Draft full-wrap mockup: companion journal path route, white-paper spine.", font=font(23), fill=gold)

    barcode_w = round(1.85 * DPI)
    barcode_h = round(1.05 * DPI)
    barcode_x = back_w - round(0.55 * DPI) - barcode_w
    barcode_y = height_px - round(0.65 * DPI) - barcode_h
    d.rounded_rectangle((barcode_x, barcode_y, barcode_x + barcode_w, barcode_y + barcode_h), radius=10, fill=(255, 255, 255, 238))
    d.text((barcode_x + 24, barcode_y + 36), "BARCODE / ISBN", font=font(24, bold=True), fill="#1f2937")
    d.text((barcode_x + 24, barcode_y + 92), "placeholder", font=font(22), fill="#374151")

    draw_spine(canvas, journal, spine_x, 0, spine_px, height_px)

    slug = f"volume-{journal.volume}-companion-journal-path-route-white-paper-full-wrap-draft"
    png_path = OUTPUT / f"{slug}.png"
    pdf_path = OUTPUT / f"{slug}.pdf"
    canvas_rgb = canvas.convert("RGB")
    canvas_rgb.save(png_path, dpi=(DPI, DPI), quality=95)
    canvas_rgb.save(pdf_path, "PDF", resolution=DPI)
    return {
        "volume": journal.volume,
        "title": journal.title,
        "pages": journal.pages,
        "spine_inches": round(journal.spine, 3),
        "cover_width_inches": round(journal.cover_width, 3),
        "cover_height_inches": 9.25,
        "png": str(png_path.relative_to(ROOT)),
        "pdf": str(pdf_path.relative_to(ROOT)),
    }


def build_contact_sheet(png_paths: list[Path]) -> Path:
    thumbs = []
    for path in png_paths:
        image = Image.open(path).convert("RGB")
        image.thumbnail((660, 466), Image.Resampling.LANCZOS)
        thumbs.append((path, image.copy()))
    width = 720
    row_height = 550
    height = len(thumbs) * row_height + 40
    sheet = Image.new("RGB", (width, height), "#f5f2eb")
    d = ImageDraw.Draw(sheet)
    y = 20
    for path, image in thumbs:
        x = (width - image.width) // 2
        sheet.paste(image, (x, y))
        y += image.height + 10
        label = path.stem.replace("-", " ").title()
        for line in textwrap.wrap(label, width=42):
            d.text((30, y), line, font=font(22, bold=True), fill="#111827")
            y += 28
        y = ((y // row_height) + 1) * row_height + 20
    out = OUTPUT / "companion-journal-full-wrap-draft-contact-sheet.png"
    sheet.save(out, dpi=(DPI, DPI))
    return out


def sync_outputs(results: list[dict[str, str | int | float]], contact_sheet: Path) -> None:
    PUBLIC_OUTPUT.mkdir(parents=True, exist_ok=True)
    SOURCE_ASSETS.mkdir(parents=True, exist_ok=True)
    PUBLIC_ASSETS.mkdir(parents=True, exist_ok=True)
    for result in results:
        for key in ("png", "pdf"):
            source = ROOT / str(result[key])
            shutil.copy2(source, PUBLIC_OUTPUT / source.name)
        png_source = ROOT / str(result["png"])
        shutil.copy2(png_source, SOURCE_ASSETS / png_source.name)
        shutil.copy2(png_source, PUBLIC_ASSETS / png_source.name)
        library_covers = PRODUCTION_LIBRARY / JOURNALS[int(result["volume"]) - 1].library_dir / "03 Covers" / "Companion Journal Full Wrap Draft"
        library_covers.mkdir(parents=True, exist_ok=True)
        shutil.copy2(png_source, library_covers / png_source.name)
        shutil.copy2(ROOT / str(result["pdf"]), library_covers / Path(str(result["pdf"])).name)
    shutil.copy2(contact_sheet, PUBLIC_OUTPUT / contact_sheet.name)
    shutil.copy2(contact_sheet, SOURCE_ASSETS / contact_sheet.name)
    shutil.copy2(contact_sheet, PUBLIC_ASSETS / contact_sheet.name)


def write_manifest(results: list[dict[str, str | int | float]], contact_sheet: Path) -> Path:
    manifest = OUTPUT / "companion-journal-full-wrap-draft-manifest.md"
    rows = [
        "# Companion Journal Full-Wrap Draft Manifest",
        "",
        "Generated: 2026-07-01",
        "",
        "These are preliminary companion journal full-wrap cover mockups for review, built from the selected Path-route cover art and current white-paper KDP working dimensions. They are not final KDP upload files until paper type, final interior page count, barcode/ISBN, trim preview, and KDP Previewer checks are locked.",
        "",
        "| Volume | Pages | Spine | Draft cover size | PNG | PDF |",
        "| --- | ---: | ---: | --- | --- | --- |",
    ]
    for result in results:
        rows.append(
            f"| Volume {result['volume']} journal | {result['pages']} | {result['spine_inches']:.3f} in | "
            f"{result['cover_width_inches']:.3f} x {result['cover_height_inches']:.3f} in | "
            f"`{Path(str(result['png'])).name}` | `{Path(str(result['pdf'])).name}` |"
        )
    rows.extend(["", f"Contact sheet: `{contact_sheet.name}`", "", "Next gate: regenerate after final page-count lock and selected KDP paper type."])
    manifest.write_text("\n".join(rows) + "\n")
    shutil.copy2(manifest, PUBLIC_OUTPUT / manifest.name)
    return manifest


def write_zip(paths: list[Path]) -> Path:
    zip_path = OUTPUT / "Lady-D-Companion-Journal-Full-Wrap-Draft-Pack.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in paths:
            zf.write(path, path.name)
    shutil.copy2(zip_path, PUBLIC_OUTPUT / zip_path.name)
    shared = PRODUCTION_LIBRARY / "_Shared" / "Release Evidence"
    shared.mkdir(parents=True, exist_ok=True)
    shutil.copy2(zip_path, shared / zip_path.name)
    return zip_path


def main() -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    results = [build_cover(journal) for journal in JOURNALS]
    png_paths = [ROOT / str(result["png"]) for result in results]
    pdf_paths = [ROOT / str(result["pdf"]) for result in results]
    contact_sheet = build_contact_sheet(png_paths)
    sync_outputs(results, contact_sheet)
    manifest = write_manifest(results, contact_sheet)
    zip_path = write_zip([*png_paths, *pdf_paths, contact_sheet, manifest])
    for result in results:
        print(result)
    print({"contact_sheet": str(contact_sheet.relative_to(ROOT)), "zip": str(zip_path.relative_to(ROOT))})


if __name__ == "__main__":
    main()
