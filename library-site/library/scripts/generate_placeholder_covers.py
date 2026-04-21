#!/usr/bin/env python3
"""
Generate placeholder cover thumbnails for all books in books.json.

Each cover is a 400x560 JPG with:
- Navy background (#1B3A5C)
- Gold border (#C9A84C)
- Arabic title rendered in Amiri-Bold
- Small year + author line at bottom

These are placeholders; real covers should be dropped into assets/covers/
using the same filename. The publish.py script will overwrite these when
you provide real cover art.
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent.parent
BOOKS_JSON = ROOT / "data" / "books.json"
COVER_DIR = ROOT / "assets" / "covers"
FONT_REG = ROOT / "assets" / "fonts" / "Amiri-Regular.ttf"
FONT_BOLD = ROOT / "assets" / "fonts" / "Amiri-Bold.ttf"

# Brand palette
NAVY = (27, 58, 92)         # #1B3A5C
GOLD = (201, 168, 76)       # #C9A84C
CREAM = (245, 240, 232)     # #F5F0E8
WHITE = (255, 255, 255)

W, H = 400, 560


def wrap_arabic(draw, text, font, max_width):
    """Wrap Arabic text to fit max_width. Returns list of lines."""
    words = text.split()
    lines = []
    current = []
    for word in words:
        test = " ".join(current + [word])
        bbox = draw.textbbox((0, 0), test, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def draw_ornament(draw, cx, cy, size=20, color=GOLD):
    """Draw a small diamond ornament centered at (cx, cy)."""
    pts = [
        (cx, cy - size // 2),
        (cx + size // 2, cy),
        (cx, cy + size // 2),
        (cx - size // 2, cy),
    ]
    draw.polygon(pts, outline=color, fill=None, width=2)
    draw.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=color)


def make_cover(book, out_path):
    """Generate one cover image for a single book entry."""
    img = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(img)

    # Inner frame
    frame_inset = 18
    draw.rectangle(
        [frame_inset, frame_inset, W - frame_inset, H - frame_inset],
        outline=GOLD, width=2
    )

    # Decorative top ornament
    draw_ornament(draw, W // 2, 58, size=22)
    draw.line([(60, 58), (W // 2 - 22, 58)], fill=GOLD, width=1)
    draw.line([(W // 2 + 22, 58), (W - 60, 58)], fill=GOLD, width=1)

    # Title (Arabic, bold, centered, wrapped)
    title_size = 34
    title_font = ImageFont.truetype(str(FONT_BOLD), title_size)
    title = book["title_ar"]

    # Shrink font if title is very long
    max_text_width = W - 80
    while True:
        lines = wrap_arabic(draw, title, title_font, max_text_width)
        if len(lines) <= 4 and title_size >= 22:
            break
        title_size -= 2
        if title_size < 22:
            break
        title_font = ImageFont.truetype(str(FONT_BOLD), title_size)

    # Vertically center the title block
    line_h = title_size + 10
    total_h = len(lines) * line_h
    y = (H - total_h) // 2 - 20
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2
        # Shadow for depth
        draw.text((x + 1, y + 1), line, font=title_font, fill=(0, 0, 0))
        draw.text((x, y), line, font=title_font, fill=GOLD)
        y += line_h

    # Subtitle (if present), smaller and cream-colored
    if book.get("subtitle_ar"):
        sub_size = 18
        sub_font = ImageFont.truetype(str(FONT_REG), sub_size)
        sub = book["subtitle_ar"]
        bbox = draw.textbbox((0, 0), sub, font=sub_font)
        tw = bbox[2] - bbox[0]
        if tw > max_text_width:
            # truncate — subtitles should be short on covers
            while tw > max_text_width and len(sub) > 10:
                sub = sub[:-1]
                bbox = draw.textbbox((0, 0), sub, font=sub_font)
                tw = bbox[2] - bbox[0]
            sub = sub + "…"
            bbox = draw.textbbox((0, 0), sub, font=sub_font)
            tw = bbox[2] - bbox[0]
        x = (W - tw) // 2
        draw.text((x, y + 10), sub, font=sub_font, fill=CREAM)

    # Decorative bottom ornament
    draw_ornament(draw, W // 2, H - 90, size=22)
    draw.line([(60, H - 90), (W // 2 - 22, H - 90)], fill=GOLD, width=1)
    draw.line([(W // 2 + 22, H - 90), (W - 60, H - 90)], fill=GOLD, width=1)

    # Author name
    author_font = ImageFont.truetype(str(FONT_REG), 18)
    author_text = "د. فضل محمد الأكوع"
    bbox = draw.textbbox((0, 0), author_text, font=author_font)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, H - 70), author_text, font=author_font, fill=CREAM)

    # Year
    year_font = ImageFont.truetype(str(FONT_BOLD), 16)
    year_text = str(book["year"])
    bbox = draw.textbbox((0, 0), year_text, font=year_font)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, H - 42), year_text, font=year_font, fill=GOLD)

    # Special case: "My Grandmother Atiqa" uses gold-on-white per the spec
    if book.get("cover_style") == "gold-on-white":
        img = Image.new("RGB", (W, H), WHITE)
        draw = ImageDraw.Draw(img)
        draw.rectangle([frame_inset, frame_inset, W - frame_inset, H - frame_inset], outline=GOLD, width=2)
        draw_ornament(draw, W // 2, 58, size=22)
        draw.line([(60, 58), (W // 2 - 22, 58)], fill=GOLD, width=1)
        draw.line([(W // 2 + 22, 58), (W - 60, 58)], fill=GOLD, width=1)
        y = (H - total_h) // 2 - 20
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=title_font)
            tw = bbox[2] - bbox[0]
            x = (W - tw) // 2
            draw.text((x, y), line, font=title_font, fill=GOLD)
            y += line_h
        if book.get("subtitle_ar"):
            sub_font = ImageFont.truetype(str(FONT_REG), 18)
            sub = book["subtitle_ar"]
            bbox = draw.textbbox((0, 0), sub, font=sub_font)
            tw = bbox[2] - bbox[0]
            draw.text(((W - tw) // 2, y + 10), sub, font=sub_font, fill=(80, 70, 40))
        draw_ornament(draw, W // 2, H - 90, size=22)
        draw.line([(60, H - 90), (W // 2 - 22, H - 90)], fill=GOLD, width=1)
        draw.line([(W // 2 + 22, H - 90), (W - 60, H - 90)], fill=GOLD, width=1)
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) // 2, H - 70), author_text, font=author_font, fill=(80, 70, 40))
        bbox = draw.textbbox((0, 0), year_text, font=year_font)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) // 2, H - 42), year_text, font=year_font, fill=GOLD)

    img.save(out_path, "JPEG", quality=88, optimize=True)


def main():
    COVER_DIR.mkdir(parents=True, exist_ok=True)
    data = json.loads(BOOKS_JSON.read_text(encoding="utf-8"))
    count = 0
    for book in data["books"]:
        cover_filename = Path(book["cover"]).name
        out_path = COVER_DIR / cover_filename
        make_cover(book, out_path)
        count += 1
        print(f"  ✓ {cover_filename}")
    print(f"\nGenerated {count} placeholder covers in {COVER_DIR}")


if __name__ == "__main__":
    main()
