#!/usr/bin/env python3
"""
produce-book.py — End-to-end book production for Dr. Fadhl Alakwaa's library.

Takes a folder of markdown chapters + metadata and produces:
  - PDF (via WeasyPrint, A5, Amiri RTL)
  - ePub (via ebooklib, RTL)
  - DOCX (via Node.js docx package with bidi:true)
  - Cover image (gold/navy, Amiri)
  - Updates books.json
  - Optionally commits and pushes

USAGE
-----
    python scripts/produce-book.py \
        --slug "halal-meat-michigan-indiana" \
        --title-ar "شراء اللحم الحلال في ميشيجان وإنديانا" \
        --title-en "Guide to Buying Halal Meat in Michigan and Indiana" \
        --subtitle-ar "متاجر، مزارع، ومعايير ذبح موثوقة" \
        --category diaspora \
        --content-dir drafts/halal-meat-michigan-indiana/ \
        --description-ar "..." \
        --description-en "..." \
        [--featured] \
        [--no-git]

CONTENT FOLDER STRUCTURE
------------------------
    drafts/halal-meat-michigan-indiana/
        ├── 00-bismillah.md         (optional)
        ├── 01-dedication.md        (optional)
        ├── 02-introduction.md
        ├── 03-chapter-1.md
        ├── 04-chapter-2.md
        ├── ...
        ├── 99-conclusion.md
        ├── meta.json               (optional - overrides CLI)
        └── cover.jpg               (optional - else auto-generated)

DEPENDENCIES
------------
  pip install weasyprint ebooklib pillow markdown
  npm install -g docx
  (Amiri fonts in assets/fonts/)
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

VALID_CATEGORIES = {"quran", "islamic", "yemen", "politics", "tech", "family", "diaspora", "personal"}
EXCLUDED_IDS = {"salman-al-awda", "wafaa-sister", "houthis-gaza-blood-power"}


def log(msg, color=""):
    """Pretty-print a status message."""
    colors = {"green": "\033[92m", "red": "\033[91m", "yellow": "\033[93m", "blue": "\033[94m", "": ""}
    end = "\033[0m" if color else ""
    print(f"{colors.get(color, '')}{msg}{end}")


def collect_content(content_dir: Path) -> list[dict]:
    """Read all .md files in order. Return list of {filename, title, body}."""
    if not content_dir.exists():
        log(f"  ✗ Content directory not found: {content_dir}", "red")
        sys.exit(1)
    chapters = []
    for md_file in sorted(content_dir.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        # First markdown heading is the chapter title
        lines = text.strip().split("\n")
        title = ""
        body = text
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                body = "\n".join(lines[lines.index(line) + 1:]).strip()
                break
        chapters.append({"file": md_file.name, "title": title, "body": body, "raw": text})
    return chapters


def build_html(chapters: list[dict], title_ar: str, subtitle_ar: str, lang: str = "ar") -> str:
    """Build a single HTML document for WeasyPrint."""
    import markdown as md_lib
    direction = "rtl" if lang == "ar" else "ltr"
    body_parts = []
    for ch in chapters:
        if ch["title"]:
            body_parts.append(f'<h2 class="chapter-title">{ch["title"]}</h2>')
        body_parts.append(md_lib.markdown(ch["body"], extensions=["extra", "toc"]))
        body_parts.append('<div class="chapter-break"></div>')
    body = "\n".join(body_parts)

    css = f"""
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
        src: url('file://{FONTS_DIR}/Amiri-Regular.ttf');
        font-weight: 400;
    }}
    @font-face {{
        font-family: 'Amiri';
        src: url('file://{FONTS_DIR}/Amiri-Bold.ttf');
        font-weight: 700;
    }}
    body {{
        font-family: 'Amiri', serif;
        font-size: 12pt;
        line-height: 1.85;
        color: #1C1C1C;
        direction: {direction};
        text-align: justify;
    }}
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
        border-{'right' if direction == 'rtl' else 'left'}: 3px solid {GOLD};
        padding: 1em 1.2em;
        margin: 1em 0;
        font-style: italic;
    }}
    .verse {{
        background: {CREAM};
        text-align: center;
        font-weight: bold;
        padding: 1em;
        margin: 1.5em 0;
        border-radius: 6px;
    }}
    """

    html = f"""<!DOCTYPE html>
<html lang="{lang}" dir="{direction}">
<head>
<meta charset="UTF-8">
<title>{title_ar}</title>
<style>{css}</style>
</head>
<body>
<h1>{title_ar}</h1>
<p style="text-align:center; color:#666;">{subtitle_ar or ''}</p>
<p style="text-align:center; color:{GOLD}; margin-top:2em;">د. فضل محمد الأكوع</p>
<div style="page-break-after: always;"></div>
{body}
</body>
</html>"""
    return html


def make_pdf(slug: str, html_ar: str, html_en: str | None) -> Path:
    """Produce PDF via WeasyPrint."""
    try:
        from weasyprint import HTML
    except ImportError:
        log("  ✗ WeasyPrint not installed. Run: pip install weasyprint", "red")
        sys.exit(1)
    out = BOOKS_DIR / f"{slug}.pdf"
    BOOKS_DIR.mkdir(parents=True, exist_ok=True)
    combined = html_ar + (html_en if html_en else "")
    HTML(string=combined, base_url=str(ROOT)).write_pdf(str(out))
    log(f"  ✓ PDF  → {out.relative_to(ROOT)}", "green")
    return out


def make_epub(slug: str, chapters: list[dict], title_ar: str, title_en: str) -> Path:
    """Produce ePub via ebooklib."""
    try:
        from ebooklib import epub
    except ImportError:
        log("  ✗ ebooklib not installed. Run: pip install ebooklib", "red")
        sys.exit(1)

    book = epub.EpubBook()
    book.set_identifier(f"alakwaa-{slug}")
    book.set_title(title_ar)
    book.set_language("ar")
    book.add_author("د. فضل محمد الأكوع")
    book.set_direction("rtl")

    items = []
    for i, ch in enumerate(chapters):
        c = epub.EpubHtml(
            title=ch["title"] or f"Chapter {i+1}",
            file_name=f"chap_{i:03}.xhtml",
            lang="ar",
            direction="rtl",
        )
        import markdown as md_lib
        body = md_lib.markdown(ch["body"], extensions=["extra"])
        c.content = f'<html dir="rtl"><body><h2>{ch["title"]}</h2>{body}</body></html>'
        book.add_item(c)
        items.append(c)

    book.toc = items
    book.spine = ["nav"] + items
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    out = BOOKS_DIR / f"{slug}.epub"
    epub.write_epub(str(out), book)
    log(f"  ✓ ePub → {out.relative_to(ROOT)}", "green")
    return out


def make_docx(slug: str, chapters: list[dict], title_ar: str) -> Path:
    """Produce DOCX via Node.js docx package."""
    # Write a temp Node.js script
    js_script = ROOT / "scripts" / "_make_docx_temp.js"
    chapters_json = json.dumps(chapters, ensure_ascii=False)
    js_code = f"""
const fs = require('fs');
const {{ Document, Packer, Paragraph, TextRun, AlignmentType, HeadingLevel, PageBreak }} = require('docx');

const chapters = {chapters_json};
const title = {json.dumps(title_ar, ensure_ascii=False)};

const NAVY = "1B3A5C", GOLD = "C9A84C";
const children = [];

children.push(new Paragraph({{
    alignment: AlignmentType.CENTER,
    children: [new TextRun({{ text: title, bold: true, size: 48, color: NAVY, rightToLeft: true }})]
}}));
children.push(new Paragraph({{
    alignment: AlignmentType.CENTER,
    children: [new TextRun({{ text: "د. فضل محمد الأكوع", size: 28, color: GOLD, rightToLeft: true }})]
}}));
children.push(new Paragraph({{ children: [new PageBreak()] }}));

for (const ch of chapters) {{
    if (ch.title) {{
        children.push(new Paragraph({{
            heading: HeadingLevel.HEADING_2,
            alignment: AlignmentType.CENTER,
            spacing: {{ before: 400, after: 240 }},
            children: [new TextRun({{ text: ch.title, bold: true, size: 32, color: NAVY, rightToLeft: true }})]
        }}));
    }}
    const paras = ch.body.split(/\\n\\n+/);
    for (const p of paras) {{
        if (!p.trim()) continue;
        children.push(new Paragraph({{
            alignment: AlignmentType.START,
            bidirectional: true,
            spacing: {{ after: 160 }},
            children: [new TextRun({{ text: p.replace(/\\n/g, ' '), size: 24, rightToLeft: true }})]
        }}));
    }}
    children.push(new Paragraph({{ children: [new PageBreak()] }}));
}}

const doc = new Document({{
    styles: {{ default: {{ document: {{ run: {{ font: "Amiri", size: 24 }} }} }} }},
    sections: [{{
        properties: {{ page: {{ size: {{ width: 8390, height: 11910 }} }} }},  // A5 in DXA
        children
    }}]
}});

Packer.toBuffer(doc).then(buf => {{
    fs.writeFileSync("{(BOOKS_DIR / f'{slug}.docx').as_posix()}", buf);
    console.log("Done");
}});
"""
    js_script.write_text(js_code, encoding="utf-8")
    result = subprocess.run(["node", str(js_script)], capture_output=True, text=True, cwd=ROOT)
    js_script.unlink(missing_ok=True)
    if result.returncode != 0:
        log(f"  ✗ DOCX failed: {result.stderr}", "red")
        return None
    out = BOOKS_DIR / f"{slug}.docx"
    log(f"  ✓ DOCX → {out.relative_to(ROOT)}", "green")
    return out


def make_cover(slug: str, title_ar: str, subtitle_ar: str) -> Path:
    """Generate the navy-gold cover via Pillow."""
    from PIL import Image, ImageDraw, ImageFont
    W, H = 800, 1120
    img = Image.new("RGB", (W, H), (27, 58, 92))
    draw = ImageDraw.Draw(img)
    draw.rectangle([36, 36, W - 36, H - 36], outline=(201, 168, 76), width=4)

    font_bold = ImageFont.truetype(str(FONTS_DIR / "Amiri-Bold.ttf"), 64)
    font_reg = ImageFont.truetype(str(FONTS_DIR / "Amiri-Regular.ttf"), 36)
    font_small = ImageFont.truetype(str(FONTS_DIR / "Amiri-Regular.ttf"), 32)

    # Title (wrap if too long)
    title = title_ar
    bbox = draw.textbbox((0, 0), title, font=font_bold)
    if bbox[2] - bbox[0] > W - 100:
        words = title.split()
        mid = len(words) // 2
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:])
        bbox1 = draw.textbbox((0, 0), line1, font=font_bold)
        bbox2 = draw.textbbox((0, 0), line2, font=font_bold)
        draw.text(((W - (bbox1[2] - bbox1[0])) // 2, H // 2 - 100), line1, font=font_bold, fill=(201, 168, 76))
        draw.text(((W - (bbox2[2] - bbox2[0])) // 2, H // 2 - 30), line2, font=font_bold, fill=(201, 168, 76))
    else:
        draw.text(((W - (bbox[2] - bbox[0])) // 2, H // 2 - 70), title, font=font_bold, fill=(201, 168, 76))

    if subtitle_ar:
        bbox = draw.textbbox((0, 0), subtitle_ar, font=font_reg)
        draw.text(((W - (bbox[2] - bbox[0])) // 2, H // 2 + 50), subtitle_ar, font=font_reg, fill=(245, 240, 232))

    author = "د. فضل محمد الأكوع"
    bbox = draw.textbbox((0, 0), author, font=font_small)
    draw.text(((W - (bbox[2] - bbox[0])) // 2, H - 140), author, font=font_small, fill=(245, 240, 232))

    year = str(datetime.now().year)
    bbox = draw.textbbox((0, 0), year, font=font_small)
    draw.text(((W - (bbox[2] - bbox[0])) // 2, H - 90), year, font=font_small, fill=(201, 168, 76))

    out = COVERS_DIR / f"{slug}.jpg"
    COVERS_DIR.mkdir(parents=True, exist_ok=True)
    img.save(out, "JPEG", quality=88, optimize=True)
    log(f"  ✓ Cover → {out.relative_to(ROOT)}", "green")
    return out


def update_manifest(slug: str, args, pages: int, formats: list[str]) -> None:
    """Add or update the entry in books.json."""
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

    # Insert at top, replacing any existing entry
    data["books"] = [b for b in data["books"] if b["id"] != slug]
    data["books"].insert(0, entry)
    data["site"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")

    BOOKS_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"  ✓ Manifest updated. Total books: {len(data['books'])}", "green")


def git_publish(slug: str, title_ar: str) -> bool:
    """Commit and push changes."""
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


def main():
    p = argparse.ArgumentParser(description="Produce a book end-to-end.")
    p.add_argument("--slug", required=True, help="kebab-case slug")
    p.add_argument("--title-ar", required=True)
    p.add_argument("--title-en", required=True)
    p.add_argument("--subtitle-ar", default="")
    p.add_argument("--category", required=True, choices=sorted(VALID_CATEGORIES))
    p.add_argument("--content-dir", required=True, help="folder with chapter .md files")
    p.add_argument("--description-ar", default="")
    p.add_argument("--description-en", default="")
    p.add_argument("--featured", action="store_true")
    p.add_argument("--no-git", action="store_true")
    p.add_argument("--cover", help="optional path to custom cover image")
    args = p.parse_args()

    if args.slug in EXCLUDED_IDS:
        log(f"✗ Slug '{args.slug}' is excluded. Refusing.", "red")
        return 2

    log(f"\n=== Producing: {args.title_ar} ({args.slug}) ===\n", "blue")

    content_dir = ROOT / args.content_dir
    chapters = collect_content(content_dir)
    log(f"  · Read {len(chapters)} chapter file(s)")

    # Cover
    if args.cover and Path(args.cover).exists():
        shutil.copy(args.cover, COVERS_DIR / f"{args.slug}.jpg")
        log(f"  ✓ Cover (provided) → assets/covers/{args.slug}.jpg", "green")
    else:
        make_cover(args.slug, args.title_ar, args.subtitle_ar)

    # Build content
    html_ar = build_html(chapters, args.title_ar, args.subtitle_ar, lang="ar")

    # Produce all 3 formats
    formats = []
    pdf = make_pdf(args.slug, html_ar, None)
    if pdf and pdf.exists():
        formats.append("pdf")
    epub = make_epub(args.slug, chapters, args.title_ar, args.title_en)
    if epub and epub.exists():
        formats.append("epub")
    docx = make_docx(args.slug, chapters, args.title_ar)
    if docx and docx.exists():
        formats.append("docx")

    # Estimate pages from PDF (if produced)
    pages = 50  # default minimum
    if pdf and pdf.exists():
        try:
            from pypdf import PdfReader
            pages = max(50, len(PdfReader(str(pdf)).pages))
        except Exception:
            pass

    # Update manifest
    update_manifest(args.slug, args, pages, formats)

    # Git push
    if not args.no_git:
        git_publish(args.slug, args.title_ar)
    else:
        log("  · Skipping git (--no-git)", "yellow")

    log(f"\n✓ Done. Live at https://fadhlyemen.github.io/library/ in ~90 seconds.\n", "green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
