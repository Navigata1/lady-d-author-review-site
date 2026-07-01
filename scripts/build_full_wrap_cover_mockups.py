#!/usr/bin/env python3
"""Build preliminary full-wrap cover mockups for the Lady D trilogy.

These are review drafts, not final KDP upload files. They use the current
white-paper spine calculations from the KDP worksheet and should be regenerated
after trim, paper, and final page counts are locked.
"""

from __future__ import annotations

import shutil
import textwrap
import zipfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "downloads" / "production" / "kdp" / "full-wrap-drafts"
PUBLIC_OUTPUT = ROOT / "public" / "downloads" / "production" / "kdp" / "full-wrap-drafts"
PUBLIC_ASSETS = ROOT / "public" / "production-assets" / "full-wrap-drafts"
PRODUCTION_LIBRARY = Path("/Users/IDC2.5/Documents/LADY D/Production Library")

DPI = 300
TRIM_W = 6.0
TRIM_H = 9.0
BLEED = 0.125
WHITE_SPINE_FACTOR = 0.002252


@dataclass(frozen=True)
class Volume:
    number: int
    title: str
    subtitle: str
    short_spine: str
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


VOLUMES = [
    Volume(
        number=1,
        title="Surrendering to God's Love",
        subtitle="A 365-Day Devotional Journey into the Father's Heart",
        short_spine="Surrendering to God's Love",
        pages=409,
        art=ROOT / "production-assets" / "cover-02-path-of-surrender-art.png",
        library_dir="01 Surrendering to God's Love",
        palette=("#172447", "#f8efd7", "#d6a64a"),
        blurb=(
            "A year of morning surrender, steady Scripture, and practical trust in "
            "the Father's love. These devotionals invite the reader to receive grace "
            "before striving, to bring real life into prayer, and to let obedience grow "
            "as a response to love."
        ),
    ),
    Volume(
        number=2,
        title="Walking with Jesus",
        subtitle="A 365-Day Devotional Journey with the Son",
        short_spine="Walking with Jesus",
        pages=350,
        art=ROOT / "production-assets" / "volume-2-cover-02-path-of-surrender-art.png",
        library_dir="02 Walking with Jesus",
        palette=("#13223f", "#fbf3dc", "#d1a044"),
        blurb=(
            "A daily discipleship path shaped by the words, mercy, nearness, and "
            "authority of Jesus. This volume helps the reader follow Christ with "
            "honest faith, practical obedience, and a heart trained by His presence."
        ),
    ),
    Volume(
        number=3,
        title="Filled with the Holy Spirit",
        subtitle="A 365-Day Devotional Journey of Power, Comfort, and Fire",
        short_spine="Filled with the Holy Spirit",
        pages=339,
        art=ROOT / "production-assets" / "volume-3-cover-02-path-of-surrender-art.png",
        library_dir="03 Filled with the Holy Spirit",
        palette=("#0d343c", "#f7f0db", "#e0a63c"),
        blurb=(
            "A year of Spirit-formed life: comfort without passivity, conviction "
            "without condemnation, power without performance, and fruit that points "
            "beyond self to Jesus."
        ),
    ),
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "Georgia Bold.ttf" if bold else "Georgia.ttf",
        "/System/Library/Fonts/Supplemental/Georgia Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Georgia.ttf",
        "/Library/Fonts/Georgia Bold.ttf" if bold else "/Library/Fonts/Georgia.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def rect_inches(x: float, y: float, w: float, h: float) -> tuple[int, int, int, int]:
    return (round(x * DPI), round(y * DPI), round((x + w) * DPI), round((y + h) * DPI))


def fit_art(path: Path, size: tuple[int, int]) -> Image.Image:
    return ImageOps.fit(Image.open(path).convert("RGB"), size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def add_vertical_gradient(image: Image.Image, top_alpha: int = 120, bottom_alpha: int = 120) -> None:
    width, height = image.size
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for y in range(height):
        top = max(0, top_alpha - int(y / max(1, height * 0.34) * top_alpha))
        bottom = max(0, bottom_alpha - int((height - y) / max(1, height * 0.34) * bottom_alpha))
        alpha = max(top, bottom)
        if alpha:
            draw.line((0, y, width, y), fill=(0, 0, 0, alpha))
    image.alpha_composite(overlay)


def draw_centered_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    box: tuple[int, int, int, int],
    face: ImageFont.FreeTypeFont,
    fill: str,
    max_chars: int,
    line_gap: int = 8,
) -> int:
    x0, y0, x1, _ = box
    lines = []
    for paragraph in text.split("\n"):
        lines.extend(textwrap.wrap(paragraph, width=max_chars) or [""])
    y = y0
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=face)
        x = x0 + ((x1 - x0) - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), line, font=face, fill=fill)
        y += (bbox[3] - bbox[1]) + line_gap
    return y


def draw_left_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    width: int,
    face: ImageFont.FreeTypeFont,
    fill: str,
    max_chars: int,
    line_gap: int = 8,
) -> int:
    x, y = xy
    for line in textwrap.wrap(text, width=max_chars):
        draw.text((x, y), line, font=face, fill=fill)
        bbox = draw.textbbox((x, y), line, font=face)
        y += (bbox[3] - bbox[1]) + line_gap
    return y


def draw_spine(canvas: Image.Image, volume: Volume, x0: int, y0: int, w: int, h: int) -> None:
    spine_layer = Image.new("RGBA", (h, w), (0, 0, 0, 0))
    d = ImageDraw.Draw(spine_layer)
    title_font = font(max(30, min(48, int(w * 0.55))), bold=True)
    author_font = font(max(20, min(30, int(w * 0.34))))
    cream = volume.palette[1]
    gold = volume.palette[2]
    d.text((round(h * 0.09), round(w * 0.18)), volume.short_spine.upper(), font=title_font, fill=cream)
    d.text((round(h * 0.72), round(w * 0.18)), "SUSAN \"LADY D\" DAMON", font=author_font, fill=gold)
    rotated = spine_layer.rotate(90, expand=True)
    canvas.alpha_composite(rotated.crop((0, 0, w, h)), (x0, y0))


def build_cover(volume: Volume) -> dict[str, str | int | float]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    width_px = round(volume.cover_width * DPI)
    height_px = round((TRIM_H + 2 * BLEED) * DPI)
    trim_px = round(TRIM_W * DPI)
    bleed_px = round(BLEED * DPI)
    spine_px = round(volume.spine * DPI)
    back_w = bleed_px + trim_px
    spine_x = back_w
    front_x = back_w + spine_px
    front_w = trim_px + bleed_px

    dark, cream, gold = volume.palette
    canvas = Image.new("RGBA", (width_px, height_px), dark)

    art_front = fit_art(volume.art, (front_w, height_px)).convert("RGBA")
    add_vertical_gradient(art_front, top_alpha=150, bottom_alpha=190)
    canvas.alpha_composite(art_front, (front_x, 0))

    art_back = fit_art(volume.art, (back_w, height_px)).convert("RGBA").filter(ImageFilter.GaussianBlur(16))
    art_back = ImageEnhance.Brightness(art_back).enhance(0.45)
    art_back = ImageEnhance.Color(art_back).enhance(0.55)
    canvas.alpha_composite(art_back, (0, 0))

    d = ImageDraw.Draw(canvas)
    d.rectangle((spine_x, 0, spine_x + spine_px, height_px), fill=dark)
    d.line((spine_x, 0, spine_x, height_px), fill=gold, width=max(2, round(DPI * 0.008)))
    d.line((spine_x + spine_px, 0, spine_x + spine_px, height_px), fill=gold, width=max(2, round(DPI * 0.008)))

    # Trim and safe-area guides are intentionally subtle for review.
    guide = (255, 255, 255, 52)
    d.rectangle(rect_inches(BLEED, BLEED, TRIM_W, TRIM_H), outline=guide, width=2)
    d.rectangle((front_x, bleed_px, front_x + trim_px, bleed_px + trim_px + round(3 * DPI)), outline=guide, width=2)

    # Front typography.
    text_x0 = front_x + round(0.48 * DPI)
    text_x1 = front_x + trim_px - round(0.48 * DPI)
    y = round(0.82 * DPI)
    d.text((text_x0, y), f"VOLUME {volume.number}", font=font(35, bold=True), fill=gold)
    y += round(0.42 * DPI)
    y = draw_centered_wrapped(
        d,
        volume.title,
        (text_x0, y, text_x1, height_px),
        font(96, bold=True),
        cream,
        max_chars=18,
        line_gap=12,
    )
    y += round(0.18 * DPI)
    draw_centered_wrapped(
        d,
        volume.subtitle,
        (text_x0, y, text_x1, height_px),
        font(34),
        cream,
        max_chars=31,
        line_gap=8,
    )
    author_y = height_px - round(0.95 * DPI)
    draw_centered_wrapped(
        d,
        'Susan "Lady D" Damon',
        (text_x0, author_y, text_x1, height_px),
        font(38, bold=True),
        cream,
        max_chars=30,
    )

    # Back-cover review copy.
    back_x = round(0.62 * DPI)
    back_y = round(0.85 * DPI)
    d.text((back_x, back_y), "LADY D DEVOTIONAL LIBRARY", font=font(33, bold=True), fill=gold)
    back_y += round(0.68 * DPI)
    d.text((back_x, back_y), volume.title, font=font(51, bold=True), fill=cream)
    back_y += round(0.56 * DPI)
    back_y = draw_left_wrapped(d, volume.blurb, (back_x, back_y), trim_px, font(34), cream, max_chars=35, line_gap=10)
    back_y += round(0.38 * DPI)
    d.text((back_x, back_y), "Includes 365 dated devotionals plus February 29 bonus material.", font=font(28), fill=cream)
    back_y += round(0.5 * DPI)
    d.text((back_x, back_y), "Draft full-wrap mockup: Path route, white-paper working spine.", font=font(24), fill=gold)

    barcode_w = round(1.85 * DPI)
    barcode_h = round(1.05 * DPI)
    barcode_x = back_w - round(0.55 * DPI) - barcode_w
    barcode_y = height_px - round(0.65 * DPI) - barcode_h
    d.rounded_rectangle((barcode_x, barcode_y, barcode_x + barcode_w, barcode_y + barcode_h), radius=10, fill=(255, 255, 255, 238))
    d.text((barcode_x + 24, barcode_y + 36), "BARCODE / ISBN", font=font(24, bold=True), fill="#1f2937")
    d.text((barcode_x + 24, barcode_y + 92), "placeholder", font=font(22), fill="#374151")

    draw_spine(canvas, volume, spine_x, 0, spine_px, height_px)

    slug = f"volume-{volume.number}-path-route-white-paper-full-wrap-draft"
    png_path = OUTPUT / f"{slug}.png"
    pdf_path = OUTPUT / f"{slug}.pdf"
    canvas_rgb = canvas.convert("RGB")
    canvas_rgb.save(png_path, dpi=(DPI, DPI), quality=95)
    canvas_rgb.save(pdf_path, "PDF", resolution=DPI)
    return {
        "volume": volume.number,
        "title": volume.title,
        "pages": volume.pages,
        "spine_inches": round(volume.spine, 3),
        "cover_width_inches": round(volume.cover_width, 3),
        "cover_height_inches": 9.25,
        "png": str(png_path.relative_to(ROOT)),
        "pdf": str(pdf_path.relative_to(ROOT)),
    }


def build_contact_sheet(png_paths: list[Path]) -> Path:
    thumbs = []
    for path in png_paths:
        image = Image.open(path).convert("RGB")
        image.thumbnail((520, 366), Image.Resampling.LANCZOS)
        thumbs.append((path, image.copy()))
    width = 580
    row_height = 460
    height = len(thumbs) * row_height + 40
    sheet = Image.new("RGB", (width, height), "#f5f2eb")
    d = ImageDraw.Draw(sheet)
    y = 20
    for path, image in thumbs:
        x = (width - image.width) // 2
        sheet.paste(image, (x, y))
        y += image.height + 10
        label = path.stem.replace("-", " ").title()
        for line in textwrap.wrap(label, width=36):
            d.text((30, y), line, font=font(22, bold=True), fill="#111827")
            y += 28
        y = ((y // row_height) + 1) * row_height + 20
    out = OUTPUT / "path-route-full-wrap-draft-contact-sheet.png"
    sheet.save(out, dpi=(DPI, DPI))
    return out


def sync_outputs(results: list[dict[str, str | int | float]], contact_sheet: Path) -> None:
    PUBLIC_OUTPUT.mkdir(parents=True, exist_ok=True)
    PUBLIC_ASSETS.mkdir(parents=True, exist_ok=True)
    for result in results:
        for key in ("png", "pdf"):
            source = ROOT / str(result[key])
            shutil.copy2(source, PUBLIC_OUTPUT / source.name)
        png_source = ROOT / str(result["png"])
        shutil.copy2(png_source, PUBLIC_ASSETS / png_source.name)
        library_covers = PRODUCTION_LIBRARY / VOLUMES[int(result["volume"]) - 1].library_dir / "03 Covers"
        library_covers.mkdir(parents=True, exist_ok=True)
        shutil.copy2(png_source, library_covers / png_source.name)
        shutil.copy2(ROOT / str(result["pdf"]), library_covers / Path(str(result["pdf"])).name)
    shutil.copy2(contact_sheet, PUBLIC_OUTPUT / contact_sheet.name)
    shutil.copy2(contact_sheet, PUBLIC_ASSETS / contact_sheet.name)


def write_manifest(results: list[dict[str, str | int | float]], contact_sheet: Path) -> Path:
    manifest = OUTPUT / "path-route-full-wrap-draft-manifest.md"
    rows = [
        "# Path Route Full-Wrap Draft Manifest",
        "",
        "Generated: 2026-07-01",
        "",
        "These are preliminary full-wrap cover mockups for review, built from the selected Path-route cover art and current white-paper KDP working dimensions. They are not final KDP upload files until paper type, final interior page count, barcode/ISBN, trim preview, and KDP previewer checks are locked.",
        "",
        "| Volume | Pages | Spine | Draft cover size | PNG | PDF |",
        "| --- | ---: | ---: | --- | --- | --- |",
    ]
    for result in results:
        rows.append(
            f"| Volume {result['volume']} | {result['pages']} | {result['spine_inches']:.3f} in | "
            f"{result['cover_width_inches']:.3f} x {result['cover_height_inches']:.3f} in | "
            f"`{Path(str(result['png'])).name}` | `{Path(str(result['pdf'])).name}` |"
        )
    rows.extend(
        [
            "",
            f"Contact sheet: `{contact_sheet.name}`",
            "",
            "Next gate: regenerate after final page-count lock and selected KDP paper type.",
        ]
    )
    manifest.write_text("\n".join(rows) + "\n")
    shutil.copy2(manifest, PUBLIC_OUTPUT / manifest.name)
    return manifest


def write_zip(paths: list[Path]) -> Path:
    zip_path = OUTPUT / "Lady-D-Path-Route-Full-Wrap-Draft-Pack.zip"
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
    results = [build_cover(volume) for volume in VOLUMES]
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
