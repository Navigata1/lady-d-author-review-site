"""Assemble inspection thumbnails of rendered PDF pages, without altering artwork."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

root = Path(__file__).resolve().parents[2] / 'quality/polish-2026-09-07'
pages = sorted((root / 'pdf-pages').glob('day-*.png'))
if len(pages) != 31:
    raise ValueError(f'Expected all 31 PDF renders; found {len(pages)}')
for start in range(0, len(pages), 8):
    sheet = Image.new('RGB', (1200, 944), '#e7ebe6')
    draw = ImageDraw.Draw(sheet)
    for i, path in enumerate(pages[start:start+8]):
        with Image.open(path) as page:
            thumb = ImageOps.contain(page.convert('RGB'), (288, 432))
            x, y = (i % 4)*300 + 6, (i // 4)*472 + 26
            sheet.paste(thumb, (x,y))
            draw.text((x,y-20), f'Day {start+i+1:02d}', fill='#19392d')
    sheet.save(root / f'pdf-contact-{start//8+1}.jpg', quality=93)
