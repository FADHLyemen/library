#!/usr/bin/env python3
"""
produce-book.py v2 — End-to-end book production for Dr. Fadhl Alakwaa's library.

STRUCTURE (every book follows this exact order):
  Front matter:
    1. Outer cover (image — top half visual, bottom half navy with gold text)
    2. Inner title page (Arabic + English titles, author, year, "First Edition")
    3. Bismillah page
    4. Dedication page (topic-matched, customized per book)
    5. AI authorship disclaimer
    6. Table of contents (Arabic)
  Arabic section (full):
    7. All Arabic chapters in order
  English section (full):
    8. Inner divider page ("English Section / القسم الإنجليزي")
    9. Table of contents (English)
   10. All English chapters in order
  Back matter:
   11. About the Book (عن الكتاب) — bilingual
   12. About the Author (عن المؤلف / About the Author) — bilingual bio
   13. Author's Other Books (مؤلفات المؤلف) — auto-generated from books.json

PRODUCES: PDF (WeasyPrint), ePub (ebooklib), DOCX (Node.js docx)

USAGE
-----
    python scripts/produce-book.py \\
        --slug "us-investment-visas-guide" \\
        --title-ar "..." --title-en "..." \\
        --subtitle-ar "..." \\
        --category diaspora \\
        --content-dir drafts/us-investment-visas-guide/ \\
        --description-ar "..." --description-en "..." \\
        --dedication-ar "..." \\
        [--featured]

CONTENT FOLDER STRUCTURE
------------------------
    drafts/<slug>/
        ar/                         <-- Arabic content
            01-introduction.md
            02-chapter-1.md
            ...
            99-conclusion.md
        en/                         <-- English content (parallel structure)
            01-introduction.md
            02-chapter-1.md
            ...
            99-conclusion.md
        cover.jpg                   <-- optional, else auto-generated
"""
from __future__ import annotations
import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOKS_JSON = ROOT / "data" / "books.json"
COVERS_DIR = ROOT / "assets" / "covers"
BOOKS_DIR = ROOT / "assets" / "books"
DRAFTS_DIR = ROOT / "drafts"
FONTS_DIR = ROOT / "assets" / "fonts"

GOLD = "#C9A84C"
NAVY = "#1B3A5C"
CREAM = "#F5F0E8"
INK = "#1C1C1C"

VALID_CATEGORIES = {"quran", "islamic", "yemen", "politics", "tech", "family", "diaspora", "personal"}
EXCLUDED_IDS = {"salman-al-awda", "wafaa-sister", "houthis-gaza-blood-power"}

AUTHOR_AR = "د. فضل محمد الأكوع"
AUTHOR_EN = "Dr. Fadhl Mohammed Alakwaa"

DISCLAIMER_AR = (
    "هذا الكتاب أُنتج بمساعدة نموذج Claude Opus 4.7 من شركة Anthropic، "
    "تحت إشراف وتوجيه المؤلف. التوجيه الفكري واختيار الموضوع والمراجعة "
    "والمسؤولية النهائية للمؤلف الدكتور فضل محمد الأكوع. الكتاب لأغراض "
    "تثقيفية وإثرائية، ولا يُغني عن استشارة المتخصصين في الموضوعات "
    "القانونية والطبية والمالية والشرعية."
)
DISCLAIMER_EN = (
    "This book was produced with the assistance of Anthropic's Claude Opus 4.7 model, "
    "under the author's direction and supervision. Intellectual direction, topic selection, "
    "review, and final responsibility rest with the author, Dr. Fadhl Mohammed Alakwaa. "
    "The book is for educational purposes and does not substitute for consultation with "
    "specialists in legal, medical, financial, or religious matters."
)

# Author bio for the "About the Author" page
BIO_AR = (
    "الدكتور فضل محمد الأكوع باحث في البيولوجيا الحاسوبية والمعلوماتية الحيوية "
    "والجينوميات المكانية بجامعة ميشيغان في آن أربر. تتمحور أبحاثه حول تطبيق "
    "الذكاء الاصطناعي في دراسة الأمراض المزمنة، ومن أبرز أعماله المنشورة دراسات "
    "على مثبطات ناقل الصوديوم-غلوكوز 2 (SGLT2) والتغيرات الأنبوبية الكلوية "
    "المنشورة في مجلة JCI عام 2023. إلى جانب مسيرته العلمية، يكتب د. فضل باللغتين "
    "العربية والإنجليزية في حقول متعددة تشمل الدراسات القرآنية، تاريخ اليمن "
    "والسياسة، الذكاء الاصطناعي والتقنية، الأسرة والتربية، ودليل المهاجرين "
    "في المهجر."
)
BIO_EN = (
    "Dr. Fadhl Mohammed Alakwaa is a researcher in computational biology, bioinformatics, "
    "and spatial genomics at the University of Michigan in Ann Arbor. His research focuses "
    "on applying AI to the study of chronic diseases; among his notable publications are "
    "studies on SGLT2 inhibitors and kidney tubular changes published in JCI in 2023. "
    "Alongside his scientific career, Dr. Alakwaa writes in both Arabic and English across "
    "fields including Quranic studies, Yemeni history and politics, AI and technology, "
    "family and parenting, and guides for diaspora life."
)


def log(msg, color=""):
    colors = {"green": "\033[92m", "red": "\033[91m", "yellow": "\033[93m", "blue": "\033[94m", "": ""}
    end = "\033[0m" if color else ""
    print(f"{colors.get(color, '')}{msg}{end}")


# ============================================================
# Content collection
# ============================================================
def collect_chapters(content_dir: Path) -> list[dict]:
    """Read all .md files in order. Return list of {filename, title, body}."""
    if not content_dir.exists():
        return []
    chapters = []
    for md_file in sorted(content_dir.glob("*.md")):
        text = md_file.read_text(encoding="utf-8").strip()
        if not text:
            continue
        lines = text.split("\n")
        title = ""
        body = text
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                # Body is everything after the heading line
                idx = lines.index(line)
                body = "\n".join(lines[idx + 1:]).strip()
                break
        chapters.append({"file": md_file.name, "title": title, "body": body})
    return chapters


# ============================================================
# Other books from manifest (for publications list)
# ============================================================
def load_other_books(current_slug: str) -> list[dict]:
    """Return all books from the manifest except this one and excluded ones."""
    if not BOOKS_JSON.exists():
        return []
    data = json.loads(BOOKS_JSON.read_text(encoding="utf-8"))
    out = []
    for b in data.get("books", []):
        if b["id"] == current_slug:
            continue
        if b["id"] in EXCLUDED_IDS:
            continue
        out.append({"title_ar": b.get("title_ar", ""), "title_en": b.get("title_en", ""), "year": b.get("year", "")})
    return out


# ============================================================
# HTML/CSS for PDF (WeasyPrint)
# ============================================================
def build_css() -> str:
    """Comprehensive CSS for the PDF. Handles RTL Arabic and LTR English with explicit direction switching."""
    return f"""
@page {{
    size: A5;
    margin: 2.2cm 2cm;
    @bottom-center {{
        content: counter(page);
        font-family: 'Amiri', serif;
        color: {GOLD};
        font-size: 10pt;
    }}
}}
@font-face {{
    font-family: 'Amiri';
    src: url('file://{FONTS_DIR}/Amiri-Regular.ttf') format('truetype');
    font-weight: 400;
}}
@font-face {{
    font-family: 'Amiri';
    src: url('file://{FONTS_DIR}/Amiri-Bold.ttf') format('truetype');
    font-weight: 700;
}}
@font-face {{
    font-family: 'Amiri';
    src: url('file://{FONTS_DIR}/Amiri-Italic.ttf') format('truetype');
    font-weight: 400;
    font-style: italic;
}}
body {{
    font-family: 'Amiri', serif;
    font-size: 12pt;
    line-height: 1.85;
    color: {INK};
    text-align: justify;
    margin: 0;
}}

/* Direction-specific sections */
.ar-section {{ direction: rtl; text-align: right; }}
.en-section {{ direction: ltr; text-align: left; font-family: 'Amiri', serif; }}
.ar-section p, .ar-section h1, .ar-section h2, .ar-section h3,
.ar-section ul, .ar-section ol, .ar-section li,
.ar-section blockquote, .ar-section table {{ direction: rtl; text-align: right; }}
.en-section p, .en-section h1, .en-section h2, .en-section h3,
.en-section ul, .en-section ol, .en-section li,
.en-section blockquote, .en-section table {{ direction: ltr; text-align: left; }}
.en-section p {{ text-align: justify; }}

/* Headings */
h1 {{
    color: {NAVY};
    font-size: 22pt;
    text-align: center;
    margin-top: 1em;
    margin-bottom: 0.4em;
}}
h2.chapter-title {{
    color: {NAVY};
    font-size: 18pt;
    text-align: center;
    margin: 1.5em 0 0.8em;
    page-break-before: always;
    border-bottom: 1px solid {GOLD};
    padding-bottom: 0.3em;
}}
h3 {{
    color: #2E75B6;
    font-size: 14pt;
    margin-top: 1.2em;
}}
.chapter-break {{ page-break-after: always; }}

blockquote {{
    background: {CREAM};
    padding: 1em 1.2em;
    margin: 1em 0;
    font-style: italic;
}}
.ar-section blockquote {{ border-right: 3px solid {GOLD}; }}
.en-section blockquote {{ border-left: 3px solid {GOLD}; }}

.verse {{
    background: {CREAM};
    text-align: center;
    font-weight: bold;
    padding: 1em;
    margin: 1.5em 0;
    border-radius: 6px;
    font-size: 14pt;
}}

/* Front matter pages - simple block layout to avoid flex split issues */
.full-page {{
    page-break-before: always;
    page-break-after: always;
    page-break-inside: avoid;
    padding-top: 5em;
}}
.cover-page {{
    page-break-after: always;
    height: 100%;
    background: {NAVY};
    color: {GOLD};
    padding: 0;
    margin: -2.2cm -2cm;
    min-height: 21cm;
    text-align: center;
}}
.cover-image-area {{
    height: 50%;
    background: linear-gradient(135deg, #2A4A6E 0%, {NAVY} 100%);
    border-bottom: 4px solid {GOLD};
}}
.cover-text-area {{
    padding: 2em 1.5em;
    direction: rtl;
}}
.cover-title-ar {{
    font-size: 26pt;
    font-weight: 700;
    color: {GOLD};
    margin: 0.4em 0;
    line-height: 1.3;
}}
.cover-subtitle-ar {{
    font-size: 14pt;
    color: white;
    margin-bottom: 0.8em;
}}
.cover-title-en {{
    font-size: 18pt;
    color: white;
    direction: ltr;
    margin: 0.6em 0;
}}
.cover-author {{
    font-size: 14pt;
    color: white;
    margin-top: 1em;
}}
.cover-year {{
    font-size: 13pt;
    color: {GOLD};
    margin-top: 0.6em;
}}
.cover-badge {{
    margin-top: 0.8em;
    font-size: 11pt;
    color: {GOLD};
    border: 1px solid {GOLD};
    display: inline-block;
    padding: 4px 14px;
    border-radius: 14px;
}}

/* Inner title page */
.inner-title {{
    text-align: center;
    direction: rtl;
}}
.inner-title h1 {{
    font-size: 28pt;
    color: {NAVY};
    margin-bottom: 0.3em;
}}
.inner-title .en-title {{
    font-size: 18pt;
    color: {GOLD};
    direction: ltr;
    font-style: italic;
    margin-bottom: 1.2em;
}}
.inner-title .subtitle {{
    font-size: 14pt;
    color: #555;
    margin-bottom: 2em;
}}
.inner-title .author {{
    font-size: 16pt;
    color: {GOLD};
    margin-top: 2em;
}}
.inner-title .year-line {{
    font-size: 12pt;
    color: #666;
    margin-top: 3em;
}}

/* Bismillah */
.bismillah {{
    text-align: center;
    direction: rtl;
    color: {GOLD};
    font-size: 28pt;
    font-weight: 700;
    margin-top: 8em;
}}

/* Dedication */
.dedication {{
    text-align: center;
    direction: rtl;
    padding: 0 1em;
}}
.dedication-label {{
    color: {GOLD};
    font-size: 16pt;
    margin-bottom: 1.5em;
    letter-spacing: 0.1em;
}}
.dedication-text {{
    color: {INK};
    font-size: 14pt;
    line-height: 2;
    font-style: italic;
}}

/* Disclaimer page */
.disclaimer-card {{
    border: 1px solid {GOLD};
    background: {CREAM};
    padding: 1.5em 1.4em;
    margin: 1em 0;
    font-size: 11pt;
    line-height: 1.7;
    color: #2A2A2A;
}}
.ar-section .disclaimer-card {{ border-right: 4px solid {GOLD}; }}
.en-section .disclaimer-card {{ border-left: 4px solid {GOLD}; }}
.disclaimer-label {{
    color: {NAVY};
    font-weight: bold;
    font-size: 13pt;
    margin-bottom: 0.6em;
    text-align: center;
}}

/* TOC */
.toc {{
    direction: rtl;
}}
.en-section .toc {{ direction: ltr; }}
.toc h2 {{
    color: {NAVY};
    font-size: 20pt;
    text-align: center;
    border-bottom: 1px solid {GOLD};
    padding-bottom: 0.3em;
    margin-bottom: 1em;
}}
.toc-item {{
    display: flex;
    justify-content: space-between;
    padding: 0.4em 0;
    border-bottom: 1px dotted #ccc;
    font-size: 12pt;
}}

/* Section dividers */
.section-divider {{
    text-align: center;
    padding-top: 8em;
}}
.section-divider .label-ar {{
    color: {GOLD};
    font-size: 32pt;
    margin-bottom: 0.4em;
    direction: rtl;
}}
.section-divider .label-en {{
    color: {NAVY};
    font-size: 22pt;
    direction: ltr;
    font-style: italic;
}}

/* Back matter */
.about-section {{
    direction: rtl;
}}
.en-section .about-section {{ direction: ltr; }}
.about-section h2 {{
    color: {NAVY};
    font-size: 20pt;
    border-bottom: 1px solid {GOLD};
    padding-bottom: 0.3em;
    margin-bottom: 1em;
}}
.publications-list {{
    direction: rtl;
    list-style: none;
    padding: 0;
}}
.publications-list li {{
    padding: 0.5em 0;
    border-bottom: 1px dotted #ddd;
    font-size: 12pt;
}}
.publications-list .pub-year {{
    color: {GOLD};
    font-weight: bold;
    margin-left: 0.5em;
    margin-right: 0.5em;
}}
"""


def render_chapters_html(chapters: list[dict], lang: str) -> str:
    """Render chapter markdown into HTML with proper direction."""
    import markdown as md_lib
    parts = []
    for ch in chapters:
        if ch["title"]:
            parts.append(f'<h2 class="chapter-title">{ch["title"]}</h2>')
        body_html = md_lib.markdown(ch["body"], extensions=["extra", "toc"])
        parts.append(body_html)
        parts.append('<div class="chapter-break"></div>')
    return "\n".join(parts)


def build_toc_html(chapters: list[dict], lang: str) -> str:
    label = "المحتويات" if lang == "ar" else "Table of Contents"
    items = []
    for i, ch in enumerate(chapters, 1):
        title = ch["title"] or (f"الفصل {i}" if lang == "ar" else f"Chapter {i}")
        items.append(f'<div class="toc-item"><span>{title}</span><span>{i}</span></div>')
    return f'<div class="full-page toc"><h2>{label}</h2>{"".join(items)}</div>'


def build_publications_list_html(other_books: list[dict], lang: str) -> str:
    """Generate the 'مؤلفات المؤلف' page."""
    label = "مؤلفات المؤلف الأخرى" if lang == "ar" else "Other Books by the Author"
    items = []
    # Sort newest first
    sorted_books = sorted(other_books, key=lambda b: b.get("year", 0), reverse=True)
    for b in sorted_books:
        title = b["title_ar"] if lang == "ar" else (b["title_en"] or b["title_ar"])
        year = b.get("year", "")
        items.append(f'<li>{title}<span class="pub-year">({year})</span></li>')
    return f'<div class="full-page about-section"><h2>{label}</h2><ul class="publications-list">{"".join(items)}</ul></div>'


def build_about_book_html(args, lang: str) -> str:
    label = "عن الكتاب" if lang == "ar" else "About this Book"
    desc = args.description_ar if lang == "ar" else args.description_en
    return f'<div class="full-page about-section"><h2>{label}</h2><p style="font-size:13pt; line-height:1.9;">{desc or ""}</p></div>'


def build_about_author_html(lang: str) -> str:
    label = "عن المؤلف" if lang == "ar" else "About the Author"
    bio = BIO_AR if lang == "ar" else BIO_EN
    return f'<div class="full-page about-section"><h2>{label}</h2><p style="font-size:13pt; line-height:1.9;">{bio}</p></div>'


def build_full_html(args, ar_chapters, en_chapters, other_books) -> str:
    """Assemble the entire bilingual book HTML in proper order."""
    css = build_css()
    year = datetime.now().year

    # Cover page
    cover = f'''
<div class="cover-page">
  <div class="cover-image-area"></div>
  <div class="cover-text-area">
    <div class="cover-title-ar">{args.title_ar}</div>
    {f'<div class="cover-subtitle-ar">{args.subtitle_ar}</div>' if args.subtitle_ar else ''}
    <div class="cover-title-en">{args.title_en}</div>
    <div class="cover-author">{AUTHOR_AR}<br/>{AUTHOR_EN}</div>
    <div class="cover-year">{year}</div>
    <div class="cover-badge">عربي · English</div>
  </div>
</div>'''

    # Inner title page
    inner_title = f'''
<div class="full-page inner-title ar-section">
  <h1>{args.title_ar}</h1>
  <div class="en-title">{args.title_en}</div>
  {f'<div class="subtitle">{args.subtitle_ar}</div>' if args.subtitle_ar else ''}
  <div class="author">{AUTHOR_AR}</div>
  <div style="color:#666; font-size:13pt; direction:ltr;">{AUTHOR_EN}</div>
  <div class="year-line">الطبعة الأولى — First Edition · {year}</div>
  <div style="color:#888; font-size:11pt; margin-top:1em;">جميع الحقوق محفوظة للمؤلف</div>
</div>'''

    # Bismillah
    bismillah = '<div class="full-page ar-section"><div class="bismillah">بسم الله الرحمن الرحيم</div></div>'

    # Dedication
    dedication_text = args.dedication_ar or "إلى روح والدي رحمه الله، وأمي حفظها الله، وزوجتي وأولادي، وإخواني وأخواتي."
    dedication = f'''
<div class="full-page ar-section dedication">
  <div class="dedication-label">إهداء</div>
  <div class="dedication-text">{dedication_text}</div>
</div>'''

    # Disclaimer page (bilingual)
    disclaimer = f'''
<div class="full-page ar-section">
  <div class="disclaimer-card">
    <div class="disclaimer-label">تنبيه</div>
    <p>{DISCLAIMER_AR}</p>
  </div>
</div>
<div class="full-page en-section">
  <div class="disclaimer-card">
    <div class="disclaimer-label">Notice</div>
    <p>{DISCLAIMER_EN}</p>
  </div>
</div>'''

    # Arabic section
    toc_ar = build_toc_html(ar_chapters, "ar")
    arabic_chapters_html = render_chapters_html(ar_chapters, "ar")
    arabic_section = f'<div class="ar-section">{toc_ar}<div>{arabic_chapters_html}</div></div>'

    # English section divider
    en_divider = '''
<div class="full-page section-divider">
  <div class="label-ar">القسم الإنجليزي</div>
  <div class="label-en">English Section</div>
</div>'''

    # English section
    toc_en = build_toc_html(en_chapters, "en") if en_chapters else ""
    english_chapters_html = render_chapters_html(en_chapters, "en") if en_chapters else ""
    english_section = f'<div class="en-section">{toc_en}<div>{english_chapters_html}</div></div>' if en_chapters else ""

    # Back matter
    about_book_ar = build_about_book_html(args, "ar")
    about_book_en = build_about_book_html(args, "en") if args.description_en else ""
    about_author_ar = build_about_author_html("ar")
    about_author_en = build_about_author_html("en")
    publications_ar = build_publications_list_html(other_books, "ar")

    back_matter = f'''
<div class="ar-section">{about_book_ar}{about_author_ar}{publications_ar}</div>
<div class="en-section">{about_book_en}{about_author_en}</div>'''

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{args.title_ar}</title>
<style>{css}</style>
</head>
<body>
{cover}
{inner_title}
{bismillah}
{dedication}
{disclaimer}
{arabic_section}
{en_divider}
{english_section}
{back_matter}
</body>
</html>"""
    return html


# ============================================================
# Cover image generation (Pillow)
# ============================================================
def make_cover_image(slug: str, title_ar: str, subtitle_ar: str) -> Path:
    from PIL import Image, ImageDraw, ImageFont
    W, H = 800, 1120
    img = Image.new("RGB", (W, H), (27, 58, 92))
    draw = ImageDraw.Draw(img)

    # Top half is the "image area" (gradient placeholder)
    for y in range(H // 2):
        ratio = y / (H // 2)
        r = int(42 + (27 - 42) * ratio)
        g = int(74 + (58 - 74) * ratio)
        b = int(110 + (92 - 110) * ratio)
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    # Gold separator
    draw.rectangle([0, H // 2 - 4, W, H // 2 + 4], fill=(201, 168, 76))

    # Frame
    draw.rectangle([20, 20, W - 20, H - 20], outline=(201, 168, 76), width=2)

    font_bold = ImageFont.truetype(str(FONTS_DIR / "Amiri-Bold.ttf"), 56)
    font_reg = ImageFont.truetype(str(FONTS_DIR / "Amiri-Regular.ttf"), 30)
    font_small = ImageFont.truetype(str(FONTS_DIR / "Amiri-Regular.ttf"), 26)
    font_en = ImageFont.truetype(str(FONTS_DIR / "Amiri-Regular.ttf"), 24)

    # Title — wraps if long, sits on lower half (bottom navy area)
    title_y = H // 2 + 60
    bbox = draw.textbbox((0, 0), title_ar, font=font_bold)
    if bbox[2] - bbox[0] > W - 80:
        words = title_ar.split()
        mid = max(1, len(words) // 2)
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:])
        for line in (line1, line2):
            bb = draw.textbbox((0, 0), line, font=font_bold)
            draw.text(((W - (bb[2] - bb[0])) // 2, title_y), line, font=font_bold, fill=(201, 168, 76))
            title_y += 70
    else:
        draw.text(((W - (bbox[2] - bbox[0])) // 2, title_y), title_ar, font=font_bold, fill=(201, 168, 76))
        title_y += 70

    # Subtitle
    if subtitle_ar:
        bbox = draw.textbbox((0, 0), subtitle_ar, font=font_reg)
        draw.text(((W - (bbox[2] - bbox[0])) // 2, title_y + 10), subtitle_ar, font=font_reg, fill=(245, 240, 232))
        title_y += 50

    # Author (Arabic + English)
    bbox = draw.textbbox((0, 0), AUTHOR_AR, font=font_small)
    draw.text(((W - (bbox[2] - bbox[0])) // 2, H - 180), AUTHOR_AR, font=font_small, fill=(245, 240, 232))
    bbox = draw.textbbox((0, 0), AUTHOR_EN, font=font_en)
    draw.text(((W - (bbox[2] - bbox[0])) // 2, H - 140), AUTHOR_EN, font=font_en, fill=(245, 240, 232))

    # Year
    year_text = str(datetime.now().year)
    bbox = draw.textbbox((0, 0), year_text, font=font_small)
    draw.text(((W - (bbox[2] - bbox[0])) // 2, H - 95), year_text, font=font_small, fill=(201, 168, 76))

    # Badge
    badge = "Arabic & English  |  عربي - إنجليزي"
    bbox = draw.textbbox((0, 0), badge, font=font_en)
    draw.text(((W - (bbox[2] - bbox[0])) // 2, H - 60), badge, font=font_en, fill=(201, 168, 76))

    out = COVERS_DIR / f"{slug}.jpg"
    COVERS_DIR.mkdir(parents=True, exist_ok=True)
    img.save(out, "JPEG", quality=88, optimize=True)
    log(f"  ✓ Cover → {out.relative_to(ROOT)}", "green")
    return out


# ============================================================
# Format generators
# ============================================================
def make_pdf(slug: str, full_html: str) -> Path:
    try:
        from weasyprint import HTML
    except ImportError:
        log("  ✗ WeasyPrint not installed. Run: pip install weasyprint", "red")
        sys.exit(1)
    out = BOOKS_DIR / f"{slug}.pdf"
    BOOKS_DIR.mkdir(parents=True, exist_ok=True)
    HTML(string=full_html, base_url=str(ROOT)).write_pdf(str(out))
    log(f"  ✓ PDF  → {out.relative_to(ROOT)}", "green")
    return out


def make_epub(slug: str, args, ar_chapters, en_chapters, other_books) -> Path:
    try:
        from ebooklib import epub
    except ImportError:
        log("  ✗ ebooklib not installed. Run: pip install ebooklib", "red")
        sys.exit(1)

    book = epub.EpubBook()
    book.set_identifier(f"alakwaa-{slug}")
    book.set_title(args.title_ar)
    book.set_language("ar")
    book.add_author(AUTHOR_AR)
    book.set_direction("rtl")

    items = []
    import markdown as md_lib

    # Title page
    title_page = epub.EpubHtml(title="Title", file_name="title.xhtml", lang="ar", direction="rtl")
    title_page.content = f'''<html dir="rtl"><body style="text-align:center;padding:3em 1em;">
<h1 style="color:#1B3A5C;font-size:2em;">{args.title_ar}</h1>
<p style="color:#C9A84C;font-style:italic;font-size:1.4em;" dir="ltr">{args.title_en}</p>
{f'<p style="color:#666;">{args.subtitle_ar}</p>' if args.subtitle_ar else ''}
<p style="color:#C9A84C;margin-top:3em;font-size:1.2em;">{AUTHOR_AR}</p>
<p style="color:#666;" dir="ltr">{AUTHOR_EN}</p>
<p style="color:#888;margin-top:2em;">الطبعة الأولى · {datetime.now().year}</p>
</body></html>'''
    book.add_item(title_page)
    items.append(title_page)

    # Bismillah
    bismillah = epub.EpubHtml(title="بسم الله", file_name="bismillah.xhtml", lang="ar", direction="rtl")
    bismillah.content = '<html dir="rtl"><body style="text-align:center;padding-top:5em;"><h1 style="color:#C9A84C;font-size:2em;">بسم الله الرحمن الرحيم</h1></body></html>'
    book.add_item(bismillah)
    items.append(bismillah)

    # Dedication
    dedication_text = args.dedication_ar or "إلى روح والدي رحمه الله، وأمي حفظها الله، وزوجتي وأولادي."
    dedication = epub.EpubHtml(title="إهداء", file_name="dedication.xhtml", lang="ar", direction="rtl")
    dedication.content = f'<html dir="rtl"><body style="text-align:center;padding:3em 1em;"><h2 style="color:#C9A84C;">إهداء</h2><p style="font-style:italic;font-size:1.2em;line-height:2;">{dedication_text}</p></body></html>'
    book.add_item(dedication)
    items.append(dedication)

    # Disclaimer (bilingual)
    disc = epub.EpubHtml(title="تنبيه — Notice", file_name="disclaimer.xhtml", lang="ar", direction="rtl")
    disc.content = f'''<html dir="rtl"><body>
<h2 style="text-align:center;color:#1B3A5C;">تنبيه</h2>
<div style="border:1px solid #C9A84C;border-right:4px solid #C9A84C;background:#F5F0E8;padding:1.5em;margin:2em 0;line-height:1.7;">
<p>{DISCLAIMER_AR}</p>
</div>
<h2 style="text-align:center;color:#1B3A5C;margin-top:3em;" dir="ltr">Notice</h2>
<div dir="ltr" style="border:1px solid #C9A84C;border-left:4px solid #C9A84C;background:#F5F0E8;padding:1.5em;margin:2em 0;line-height:1.7;">
<p>{DISCLAIMER_EN}</p>
</div>
</body></html>'''
    book.add_item(disc)
    items.append(disc)

    # Arabic chapters
    for i, ch in enumerate(ar_chapters):
        c = epub.EpubHtml(title=ch["title"] or f"Chapter {i+1}",
                          file_name=f"ar_chap_{i:03}.xhtml", lang="ar", direction="rtl")
        body = md_lib.markdown(ch["body"], extensions=["extra"])
        c.content = f'<html dir="rtl"><body><h2 style="color:#1B3A5C;">{ch["title"]}</h2>{body}</body></html>'
        book.add_item(c)
        items.append(c)

    # English section divider
    if en_chapters:
        divider = epub.EpubHtml(title="English Section", file_name="en_divider.xhtml", lang="en", direction="ltr")
        divider.content = '<html dir="ltr"><body style="text-align:center;padding-top:5em;"><h1 style="color:#1B3A5C;">English Section</h1><p style="color:#C9A84C;" dir="rtl">القسم الإنجليزي</p></body></html>'
        book.add_item(divider)
        items.append(divider)

        for i, ch in enumerate(en_chapters):
            c = epub.EpubHtml(title=ch["title"] or f"Chapter {i+1}",
                              file_name=f"en_chap_{i:03}.xhtml", lang="en", direction="ltr")
            body = md_lib.markdown(ch["body"], extensions=["extra"])
            c.content = f'<html dir="ltr"><body><h2 style="color:#1B3A5C;">{ch["title"]}</h2>{body}</body></html>'
            book.add_item(c)
            items.append(c)

    # Back matter
    about_book = epub.EpubHtml(title="عن الكتاب — About this Book", file_name="about_book.xhtml", lang="ar", direction="rtl")
    about_book.content = f'''<html dir="rtl"><body>
<h2 style="color:#1B3A5C;">عن الكتاب</h2><p style="line-height:1.9;">{args.description_ar or ""}</p>
<h2 dir="ltr" style="color:#1B3A5C;margin-top:3em;">About this Book</h2>
<p dir="ltr" style="line-height:1.9;">{args.description_en or ""}</p>
</body></html>'''
    book.add_item(about_book)
    items.append(about_book)

    about_author = epub.EpubHtml(title="عن المؤلف — About the Author", file_name="about_author.xhtml", lang="ar", direction="rtl")
    about_author.content = f'''<html dir="rtl"><body>
<h2 style="color:#1B3A5C;">عن المؤلف</h2><p style="line-height:1.9;">{BIO_AR}</p>
<h2 dir="ltr" style="color:#1B3A5C;margin-top:3em;">About the Author</h2>
<p dir="ltr" style="line-height:1.9;">{BIO_EN}</p>
</body></html>'''
    book.add_item(about_author)
    items.append(about_author)

    if other_books:
        sorted_books = sorted(other_books, key=lambda b: b.get("year", 0), reverse=True)
        pubs_items = "".join(f'<li style="padding:0.4em 0;border-bottom:1px dotted #ddd;">{b["title_ar"]} <span style="color:#C9A84C;">({b.get("year","")})</span></li>' for b in sorted_books)
        pubs = epub.EpubHtml(title="مؤلفات المؤلف", file_name="publications.xhtml", lang="ar", direction="rtl")
        pubs.content = f'<html dir="rtl"><body><h2 style="color:#1B3A5C;">مؤلفات المؤلف الأخرى</h2><ul style="list-style:none;padding:0;">{pubs_items}</ul></body></html>'
        book.add_item(pubs)
        items.append(pubs)

    book.toc = items
    book.spine = ["nav"] + items
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    out = BOOKS_DIR / f"{slug}.epub"
    epub.write_epub(str(out), book)
    log(f"  ✓ ePub → {out.relative_to(ROOT)}", "green")
    return out


def make_docx(slug: str, args, ar_chapters, en_chapters, other_books) -> Path:
    """Produce DOCX via Node.js docx package."""
    js_script = ROOT / "scripts" / "_make_docx_temp.js"

    payload = {
        "slug": slug,
        "title_ar": args.title_ar,
        "title_en": args.title_en,
        "subtitle_ar": args.subtitle_ar or "",
        "dedication_ar": args.dedication_ar or "إلى روح والدي رحمه الله، وأمي حفظها الله، وزوجتي وأولادي.",
        "description_ar": args.description_ar or "",
        "description_en": args.description_en or "",
        "ar_chapters": ar_chapters,
        "en_chapters": en_chapters,
        "other_books": sorted(other_books, key=lambda b: b.get("year", 0), reverse=True),
        "year": datetime.now().year,
        "disclaimer_ar": DISCLAIMER_AR,
        "disclaimer_en": DISCLAIMER_EN,
        "bio_ar": BIO_AR,
        "bio_en": BIO_EN,
        "author_ar": AUTHOR_AR,
        "author_en": AUTHOR_EN,
        "out_path": (BOOKS_DIR / f"{slug}.docx").as_posix(),
    }

    js_code = """
const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, AlignmentType, HeadingLevel, PageBreak, BorderStyle, ShadingType } = require('docx');

const data = """ + json.dumps(payload, ensure_ascii=False) + """;

const NAVY = "1B3A5C", GOLD = "C9A84C", CREAM = "F5F0E8";
const children = [];

const center = (opts) => ({ alignment: AlignmentType.CENTER, ...opts });
const arPara = (text, opts = {}) => new Paragraph({
    alignment: opts.align || AlignmentType.START,
    bidirectional: true,
    spacing: opts.spacing || { after: 160 },
    children: [new TextRun({ text, size: opts.size || 24, bold: opts.bold, color: opts.color, rightToLeft: true })]
});
const enPara = (text, opts = {}) => new Paragraph({
    alignment: opts.align || AlignmentType.LEFT,
    spacing: opts.spacing || { after: 160 },
    children: [new TextRun({ text, size: opts.size || 22, bold: opts.bold, color: opts.color })]
});
const pageBreak = () => new Paragraph({ children: [new PageBreak()] });

// === FRONT MATTER ===

// Inner title page (DOCX can't render an image cover practically — use formatted title)
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 2400, after: 240 },
    children: [new TextRun({ text: data.title_ar, bold: true, size: 56, color: NAVY, rightToLeft: true })]}));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 },
    children: [new TextRun({ text: data.title_en, italics: true, size: 36, color: GOLD })]}));
if (data.subtitle_ar) children.push(arPara(data.subtitle_ar, { align: AlignmentType.CENTER, size: 26, color: "666666", spacing: { after: 800 }}));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 },
    children: [new TextRun({ text: data.author_ar, size: 32, color: GOLD, rightToLeft: true })]}));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 600 },
    children: [new TextRun({ text: data.author_en, size: 28, color: "666666" })]}));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 800 },
    children: [new TextRun({ text: `الطبعة الأولى — First Edition · ${data.year}`, size: 20, color: "888888", rightToLeft: true })]}));
children.push(arPara("جميع الحقوق محفوظة للمؤلف", { align: AlignmentType.CENTER, size: 18, color: "888888" }));
children.push(pageBreak());

// Bismillah
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 4800, after: 400 },
    children: [new TextRun({ text: "بسم الله الرحمن الرحيم", bold: true, size: 56, color: GOLD, rightToLeft: true })]}));
children.push(pageBreak());

// Dedication
children.push(arPara("إهداء", { align: AlignmentType.CENTER, size: 32, color: GOLD, spacing: { before: 2400, after: 600 } }));
children.push(arPara(data.dedication_ar, { align: AlignmentType.CENTER, size: 26, spacing: { after: 200 } }));
children.push(pageBreak());

// Disclaimer
children.push(arPara("تنبيه", { align: AlignmentType.CENTER, size: 32, bold: true, color: NAVY, spacing: { before: 1200, after: 400 } }));
children.push(new Paragraph({
    alignment: AlignmentType.START, bidirectional: true, spacing: { after: 400 },
    border: {
        top: { style: BorderStyle.SINGLE, size: 8, color: GOLD, space: 8 },
        bottom: { style: BorderStyle.SINGLE, size: 8, color: GOLD, space: 8 },
        left: { style: BorderStyle.SINGLE, size: 8, color: GOLD, space: 8 },
        right: { style: BorderStyle.SINGLE, size: 24, color: GOLD, space: 8 }
    },
    shading: { fill: CREAM, type: ShadingType.CLEAR, color: "auto" },
    children: [new TextRun({ text: data.disclaimer_ar, size: 22, rightToLeft: true })]
}));
children.push(enPara("Notice", { align: AlignmentType.CENTER, size: 32, bold: true, color: NAVY, spacing: { before: 600, after: 200 } }));
children.push(new Paragraph({
    alignment: AlignmentType.LEFT, spacing: { after: 400 },
    border: {
        top: { style: BorderStyle.SINGLE, size: 8, color: GOLD, space: 8 },
        bottom: { style: BorderStyle.SINGLE, size: 8, color: GOLD, space: 8 },
        left: { style: BorderStyle.SINGLE, size: 24, color: GOLD, space: 8 },
        right: { style: BorderStyle.SINGLE, size: 8, color: GOLD, space: 8 }
    },
    shading: { fill: CREAM, type: ShadingType.CLEAR, color: "auto" },
    children: [new TextRun({ text: data.disclaimer_en, size: 20 })]
}));
children.push(pageBreak());

// === ARABIC SECTION ===
for (const ch of data.ar_chapters) {
    if (ch.title) {
        children.push(arPara(ch.title, {
            align: AlignmentType.CENTER, size: 36, bold: true, color: NAVY,
            spacing: { before: 600, after: 360 }
        }));
    }
    const paras = ch.body.split(/\\n\\n+/);
    for (const p of paras) {
        if (!p.trim()) continue;
        children.push(arPara(p.replace(/\\n/g, ' '), { size: 24 }));
    }
    children.push(pageBreak());
}

// === ENGLISH SECTION DIVIDER ===
if (data.en_chapters && data.en_chapters.length > 0) {
    children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 3600 },
        children: [new TextRun({ text: "English Section", size: 48, bold: true, color: NAVY })]}));
    children.push(arPara("القسم الإنجليزي", { align: AlignmentType.CENTER, size: 36, color: GOLD, spacing: { after: 400 } }));
    children.push(pageBreak());

    for (const ch of data.en_chapters) {
        if (ch.title) {
            children.push(enPara(ch.title, {
                align: AlignmentType.CENTER, size: 36, bold: true, color: NAVY,
                spacing: { before: 600, after: 360 }
            }));
        }
        const paras = ch.body.split(/\\n\\n+/);
        for (const p of paras) {
            if (!p.trim()) continue;
            children.push(enPara(p.replace(/\\n/g, ' '), { size: 22 }));
        }
        children.push(pageBreak());
    }
}

// === BACK MATTER ===
// About the Book
children.push(arPara("عن الكتاب", { align: AlignmentType.CENTER, size: 36, bold: true, color: NAVY, spacing: { before: 600, after: 400 } }));
if (data.description_ar) children.push(arPara(data.description_ar, { size: 24 }));
if (data.description_en) {
    children.push(enPara("About this Book", { align: AlignmentType.CENTER, size: 36, bold: true, color: NAVY, spacing: { before: 800, after: 400 } }));
    children.push(enPara(data.description_en, { size: 22 }));
}
children.push(pageBreak());

// About the Author
children.push(arPara("عن المؤلف", { align: AlignmentType.CENTER, size: 36, bold: true, color: NAVY, spacing: { before: 600, after: 400 } }));
children.push(arPara(data.bio_ar, { size: 24 }));
children.push(enPara("About the Author", { align: AlignmentType.CENTER, size: 36, bold: true, color: NAVY, spacing: { before: 800, after: 400 } }));
children.push(enPara(data.bio_en, { size: 22 }));
children.push(pageBreak());

// Publications
if (data.other_books && data.other_books.length > 0) {
    children.push(arPara("مؤلفات المؤلف الأخرى", { align: AlignmentType.CENTER, size: 36, bold: true, color: NAVY, spacing: { before: 600, after: 400 } }));
    for (const b of data.other_books) {
        children.push(new Paragraph({
            alignment: AlignmentType.START, bidirectional: true, spacing: { after: 80 },
            children: [
                new TextRun({ text: `• ${b.title_ar} `, size: 22, rightToLeft: true }),
                new TextRun({ text: `(${b.year || ''})`, size: 20, color: GOLD })
            ]
        }));
    }
}

const doc = new Document({
    styles: { default: { document: { run: { font: "Amiri", size: 24 } } } },
    sections: [{
        properties: { page: { size: { width: 8390, height: 11910 } } },
        children
    }]
});

Packer.toBuffer(doc).then(buf => {
    fs.writeFileSync(data.out_path, buf);
    console.log("Done");
});
"""

    js_script.write_text(js_code, encoding="utf-8")
    result = subprocess.run(["node", str(js_script)], capture_output=True, text=True, cwd=ROOT)
    try:
        js_script.unlink(missing_ok=True)
    except (PermissionError, OSError) as e:
        log(f"  · Could not delete temp file (non-fatal): {e}", "yellow")
    if result.returncode != 0:
        log(f"  ✗ DOCX failed: {result.stderr}", "red")
        return None
    out = BOOKS_DIR / f"{slug}.docx"
    log(f"  ✓ DOCX → {out.relative_to(ROOT)}", "green")
    return out


# ============================================================
# Manifest update + git
# ============================================================
def update_manifest(slug: str, args, pages: int, formats: list[str]):
    data = json.loads(BOOKS_JSON.read_text(encoding="utf-8"))
    files = {fmt: f"assets/books/{slug}.{fmt}" for fmt in formats}
    entry = {
        "id": slug,
        "title_ar": args.title_ar,
        "title_en": args.title_en,
        "subtitle_ar": args.subtitle_ar or "",
        "category": args.category,
        "year": datetime.now().year,
        "pages": pages,
        "description_ar": args.description_ar or "",
        "description_en": args.description_en or "",
        "cover": f"assets/covers/{slug}.jpg",
        "files": files,
        "formats": formats,
        "featured": bool(args.featured),
    }
    data["books"] = [b for b in data["books"] if b["id"] != slug]
    data["books"].insert(0, entry)
    data["site"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    BOOKS_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"  ✓ Manifest updated. Total books: {len(data['books'])}", "green")


def git_publish(slug: str, title_ar: str) -> bool:
    paths = [
        "data/books.json",
        f"assets/covers/{slug}.jpg",
        f"assets/books/{slug}.pdf",
        f"assets/books/{slug}.epub",
        f"assets/books/{slug}.docx",
    ]
    existing = [p for p in paths if (ROOT / p).exists()]
    subprocess.run(["git", "add", "--", *existing], cwd=ROOT, check=False)
    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT)
    if diff.returncode == 0:
        log("  · No changes to commit", "yellow")
        return True
    msg = f"add: {title_ar} ({slug})"
    commit = subprocess.run(["git", "commit", "-m", msg], cwd=ROOT, capture_output=True, text=True)
    if commit.returncode != 0:
        log(f"  ✗ Commit failed: {commit.stderr}", "red")
        return False
    log(f"  ✓ Committed: {msg}", "green")
    push = subprocess.run(["git", "push", "origin", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    if push.returncode != 0:
        log(f"  ⚠ Push failed: {push.stderr}", "yellow")
        return False
    log("  ✓ Pushed → live in ~90 seconds", "green")
    return True


# ============================================================
# Main
# ============================================================
def main():
    p = argparse.ArgumentParser(description="Produce a book end-to-end.")
    p.add_argument("--slug", required=True)
    p.add_argument("--title-ar", required=True)
    p.add_argument("--title-en", required=True)
    p.add_argument("--subtitle-ar", default="")
    p.add_argument("--category", required=True, choices=sorted(VALID_CATEGORIES))
    p.add_argument("--content-dir", required=True,
                   help="folder containing ar/ and en/ subfolders with chapter .md files")
    p.add_argument("--description-ar", default="")
    p.add_argument("--description-en", default="")
    p.add_argument("--dedication-ar", default="",
                   help="topic-matched dedication; if empty, uses default family dedication")
    p.add_argument("--featured", action="store_true")
    p.add_argument("--no-git", action="store_true")
    args = p.parse_args()

    if args.slug in EXCLUDED_IDS:
        log(f"✗ Slug '{args.slug}' is excluded.", "red")
        return 2

    log(f"\n=== Producing: {args.title_ar} ({args.slug}) ===\n", "blue")

    content_dir = ROOT / args.content_dir
    ar_dir = content_dir / "ar"
    en_dir = content_dir / "en"

    # Backwards compat: if no ar/en subfolders, treat content_dir as Arabic
    if not ar_dir.exists() and not en_dir.exists():
        log(f"  ⚠ No ar/ or en/ subfolders. Treating {content_dir} as Arabic.", "yellow")
        ar_chapters = collect_chapters(content_dir)
        en_chapters = []
    else:
        ar_chapters = collect_chapters(ar_dir)
        en_chapters = collect_chapters(en_dir)

    log(f"  · Arabic chapters: {len(ar_chapters)}")
    log(f"  · English chapters: {len(en_chapters)}")

    if not ar_chapters:
        log(f"  ✗ No Arabic chapters found. Aborting.", "red")
        return 2

    # Cover
    make_cover_image(args.slug, args.title_ar, args.subtitle_ar)

    # Get other books for publications list
    other_books = load_other_books(args.slug)

    # Build full HTML
    full_html = build_full_html(args, ar_chapters, en_chapters, other_books)

    # Produce all formats
    formats = []
    pdf = make_pdf(args.slug, full_html)
    if pdf and pdf.exists():
        formats.append("pdf")
    epub = make_epub(args.slug, args, ar_chapters, en_chapters, other_books)
    if epub and epub.exists():
        formats.append("epub")
    docx = make_docx(args.slug, args, ar_chapters, en_chapters, other_books)
    if docx and docx.exists():
        formats.append("docx")

    # Page count from PDF
    pages = 50
    if pdf and pdf.exists():
        try:
            from pypdf import PdfReader
            pages = max(50, len(PdfReader(str(pdf)).pages))
        except Exception:
            pass

    update_manifest(args.slug, args, pages, formats)

    if not args.no_git:
        git_publish(args.slug, args.title_ar)
    else:
        log("  · Skipping git (--no-git)", "yellow")

    log(f"\n✓ Done. Live at https://fadhlyemen.github.io/library/ in ~90 seconds.\n", "green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
