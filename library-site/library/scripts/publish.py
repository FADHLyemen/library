#!/usr/bin/env python3
"""
publish.py — One-command book publishing for the Dr. Fadhl Alakwaa Library.

Takes a finished book (PDF + ePub + DOCX + cover) and:
  1. Copies the files into assets/books/ and assets/covers/
  2. Appends a new entry to data/books.json (or updates an existing one)
  3. Commits the change to Git and pushes to origin/main
  4. GitHub Pages auto-rebuilds within ~1 minute

USAGE
-----
    python publish.py \
        --id "how-llms-work" \
        --title-ar "كيف تعمل النماذج اللغوية الكبيرة" \
        --title-en "How Large Language Models Work" \
        --subtitle-ar "دليل مبسّط" \
        --category tech \
        --pages 65 \
        --pdf  /mnt/user-data/outputs/how-llms-work.pdf \
        --epub /mnt/user-data/outputs/how-llms-work.epub \
        --docx /mnt/user-data/outputs/how-llms-work.docx \
        --cover /mnt/user-data/outputs/how-llms-work-cover.png \
        --description-ar "شرح مبسط لكيفية عمل النماذج اللغوية..." \
        --description-en "A simplified explanation of how LLMs work..." \
        --featured

Or interactively, with no arguments — the script will prompt for each field.

REQUIREMENTS
------------
  pip install pillow
  git configured on the machine, with push access to the repo

AUTHOR DEFAULTS
---------------
If a field is missing, sensible defaults are used. The author name is
always "Dr. Fadhl Mohammed Alakwaa" / "د. فضل محمد الأكوع".
"""

from __future__ import annotations
import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ----------------------------------------------------------
# Paths
# ----------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
BOOKS_JSON = ROOT / "data" / "books.json"
COVERS_DIR = ROOT / "assets" / "covers"
BOOKS_DIR = ROOT / "assets" / "books"

VALID_CATEGORIES = {
    "quran", "islamic", "yemen", "politics",
    "tech", "family", "diaspora", "personal"
}

EXCLUDED_IDS = {"salman-al-awda"}  # never publish this book

COVER_MAX_W = 800  # resize covers so the site loads fast


# ----------------------------------------------------------
# Helpers
# ----------------------------------------------------------
def load_manifest() -> dict:
    return json.loads(BOOKS_JSON.read_text(encoding="utf-8"))


def save_manifest(data: dict) -> None:
    data["site"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    BOOKS_JSON.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def copy_with_resize(src: Path, dst: Path, is_image: bool = False) -> None:
    """Copy a file into the repo. For images, optionally downscale."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if is_image and HAS_PIL:
        img = Image.open(src)
        if img.width > COVER_MAX_W:
            ratio = COVER_MAX_W / img.width
            new_h = int(img.height * ratio)
            img = img.resize((COVER_MAX_W, new_h), Image.LANCZOS)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(dst, "JPEG", quality=88, optimize=True)
    else:
        shutil.copy2(src, dst)


def run_git(*args) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def git_commit_and_push(book_id: str, book_title: str) -> bool:
    """Commit and push the new book to origin/main. Returns success bool."""
    # Only stage what this script touched
    paths_to_add = [
        str(BOOKS_JSON.relative_to(ROOT)),
        f"assets/covers/{book_id}.jpg",
        f"assets/books/{book_id}.pdf",
        f"assets/books/{book_id}.epub",
        f"assets/books/{book_id}.docx",
    ]
    # Filter to paths that actually exist
    existing = [p for p in paths_to_add if (ROOT / p).exists()]
    add = run_git("add", "--", *existing)
    if add.returncode != 0:
        print(f"  ⚠ git add failed: {add.stderr.strip()}")
        return False

    # Check if anything was actually staged
    diff = run_git("diff", "--cached", "--quiet")
    if diff.returncode == 0:
        print("  · no changes to commit (already up to date)")
        return True

    msg = f"add: {book_title} ({book_id})"
    commit = run_git("commit", "-m", msg)
    if commit.returncode != 0:
        print(f"  ⚠ git commit failed: {commit.stderr.strip()}")
        return False
    print(f"  ✓ committed: {msg}")

    push = run_git("push", "origin", "HEAD")
    if push.returncode != 0:
        print(f"  ⚠ git push failed: {push.stderr.strip()}")
        print("  → Your commit is local. Run `git push` when ready.")
        return False
    print("  ✓ pushed to origin — GitHub Pages will rebuild in ~1 minute")
    return True


# ----------------------------------------------------------
# Main publishing flow
# ----------------------------------------------------------
def publish(args: argparse.Namespace) -> int:
    if args.id in EXCLUDED_IDS:
        print(f"✗ ID '{args.id}' is on the excluded list. Refusing to publish.")
        return 2

    if args.category not in VALID_CATEGORIES:
        print(f"✗ Invalid category '{args.category}'. "
              f"Must be one of: {', '.join(sorted(VALID_CATEGORIES))}")
        return 2

    data = load_manifest()
    books = data["books"]

    # Check for existing entry (update vs insert)
    existing_idx = next((i for i, b in enumerate(books) if b["id"] == args.id), None)
    is_update = existing_idx is not None

    # --- Copy files ---
    formats = []
    files = {}

    if args.cover and Path(args.cover).exists():
        cover_dst = COVERS_DIR / f"{args.id}.jpg"
        copy_with_resize(Path(args.cover), cover_dst, is_image=True)
        print(f"  ✓ cover → {cover_dst.relative_to(ROOT)}")

    if args.pdf and Path(args.pdf).exists():
        dst = BOOKS_DIR / f"{args.id}.pdf"
        copy_with_resize(Path(args.pdf), dst)
        files["pdf"] = f"assets/books/{args.id}.pdf"
        formats.append("pdf")
        print(f"  ✓ pdf   → {dst.relative_to(ROOT)}")

    if args.epub and Path(args.epub).exists():
        dst = BOOKS_DIR / f"{args.id}.epub"
        copy_with_resize(Path(args.epub), dst)
        files["epub"] = f"assets/books/{args.id}.epub"
        formats.append("epub")
        print(f"  ✓ epub  → {dst.relative_to(ROOT)}")

    if args.docx and Path(args.docx).exists():
        dst = BOOKS_DIR / f"{args.id}.docx"
        copy_with_resize(Path(args.docx), dst)
        files["docx"] = f"assets/books/{args.id}.docx"
        formats.append("docx")
        print(f"  ✓ docx  → {dst.relative_to(ROOT)}")

    # --- Build/merge the manifest entry ---
    entry = {
        "id": args.id,
        "title_ar": args.title_ar,
        "title_en": args.title_en,
        "subtitle_ar": args.subtitle_ar or "",
        "category": args.category,
        "year": args.year,
        "pages": args.pages,
        "description_ar": args.description_ar or "",
        "description_en": args.description_en or "",
        "cover": f"assets/covers/{args.id}.jpg",
        "files": files or {"pdf": f"assets/books/{args.id}.pdf"},
        "formats": formats if formats else ["pdf"],
        "featured": bool(args.featured),
    }

    if is_update:
        # Preserve any existing non-overwritten fields
        existing = books[existing_idx]
        merged = {**existing, **{k: v for k, v in entry.items() if v not in ("", None, [])}}
        books[existing_idx] = merged
        action = "updated"
    else:
        books.insert(0, entry)  # newest first
        action = "added"

    save_manifest(data)
    print(f"  ✓ books.json {action}: {args.title_ar} ({args.id})")

    # --- Git commit + push ---
    if not args.no_git:
        git_commit_and_push(args.id, args.title_ar)
    else:
        print("  · skipping git (--no-git)")

    print(f"\n✓ Done. Library now has {len(books)} books.")
    if not args.no_git:
        print(f"  Live at: {data['site']['base_url']}")
    return 0


def prompt(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"{label}{suffix}: ").strip()
    return val or default


def interactive_args() -> argparse.Namespace:
    """Prompt the user for each field, for when no CLI args are passed."""
    print("=" * 60)
    print("Add a new book to the library")
    print("=" * 60)
    a = argparse.Namespace()
    a.id = prompt("Book ID (kebab-case, e.g. 'how-llms-work')")
    a.title_ar = prompt("Arabic title")
    a.title_en = prompt("English title")
    a.subtitle_ar = prompt("Arabic subtitle (optional)", "")
    a.category = prompt(f"Category ({'/'.join(sorted(VALID_CATEGORIES))})")
    a.year = int(prompt("Year", str(datetime.now().year)))
    a.pages = int(prompt("Pages", "0"))
    a.description_ar = prompt("Arabic description (1-2 sentences)", "")
    a.description_en = prompt("English description (1-2 sentences)", "")
    a.pdf = prompt("PDF path (optional)", "")
    a.epub = prompt("ePub path (optional)", "")
    a.docx = prompt("DOCX path (optional)", "")
    a.cover = prompt("Cover image path (PNG/JPG)")
    a.featured = prompt("Featured? (y/N)", "n").lower().startswith("y")
    a.no_git = prompt("Skip git push? (y/N)", "n").lower().startswith("y")
    return a


def main():
    p = argparse.ArgumentParser(description="Publish a book to the library.")
    p.add_argument("--id", help="kebab-case book ID")
    p.add_argument("--title-ar", help="Arabic title")
    p.add_argument("--title-en", help="English title")
    p.add_argument("--subtitle-ar", default="")
    p.add_argument("--category", help=f"one of {sorted(VALID_CATEGORIES)}")
    p.add_argument("--year", type=int, default=datetime.now().year)
    p.add_argument("--pages", type=int, default=0)
    p.add_argument("--description-ar", default="")
    p.add_argument("--description-en", default="")
    p.add_argument("--pdf", default="")
    p.add_argument("--epub", default="")
    p.add_argument("--docx", default="")
    p.add_argument("--cover", help="path to cover image")
    p.add_argument("--featured", action="store_true")
    p.add_argument("--no-git", action="store_true", help="skip commit+push")
    args = p.parse_args()

    # If no args, enter interactive mode
    if not args.id:
        args = interactive_args()

    required = ["id", "title_ar", "title_en", "category"]
    missing = [f for f in required if not getattr(args, f)]
    if missing:
        print(f"✗ Missing required fields: {', '.join(missing)}")
        return 2

    return publish(args)


if __name__ == "__main__":
    sys.exit(main())
