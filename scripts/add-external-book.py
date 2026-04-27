#!/usr/bin/env python3
"""
add-external-book.py — Adds a pre-built book to the library manifest.

Use this when you've produced a book outside the standard pipeline (e.g., 
in another Claude account) and just need to register it in books.json.

USAGE:
    python scripts/add-external-book.py

The script is hardcoded for the specific book being added. Edit the BOOK_ENTRY 
dict at the top to change details.

What it does:
1. Reads books.json
2. Removes any existing entry with the same slug (so re-runs are safe)
3. Inserts the new entry at the top of the books array
4. Updates last_updated date
5. Writes back as UTF-8 with proper formatting

Does NOT:
- Move or rename your book files (you do that yourself in PowerShell)
- Push to git (you do that yourself after reviewing)
"""
import json
import sys
from datetime import datetime
from pathlib import Path

# =============================================================================
# Edit this dict to change the book being added
# =============================================================================
BOOK_ENTRY = {
    "id": "sunni-shia-rapprochement",
    "title_ar": "التقارب السني الشيعي",
    "title_en": "Sunni–Shia Rapprochement",
    "subtitle_ar": "بين الجوهر الديني والصراع السياسي",
    "category": "islamic",
    "year": 2026,
    "pages": 86,
    "description_ar": (
        "دراسة تحليلية معمّقة للعلاقة بين المذهبين السني والشيعي، "
        "تكشف الفروق الجوهرية من الفرعية، وتُشرّح الأسباب الحقيقية "
        "للخلاف بين الديني والسياسي، ودور القوى الخارجية في تأجيج "
        "الصراع، وتطرح طريقاً واقعياً للتقارب."
    ),
    "description_en": (
        "An in-depth analytical study of the Sunni–Shia relationship that "
        "distinguishes substantive doctrinal differences from secondary ones, "
        "anatomizes the true religious-versus-political causes of conflict, "
        "examines the role of external powers in fueling division, and "
        "presents a realistic path toward genuine rapprochement."
    ),
    "cover": "assets/covers/sunni-shia-rapprochement.jpg",
    "files": {
        "pdf": "assets/books/sunni-shia-rapprochement.pdf",
        "epub": "assets/books/sunni-shia-rapprochement.epub",
        "docx": "assets/books/sunni-shia-rapprochement.docx",
    },
    "formats": ["pdf", "epub", "docx"],
}
# =============================================================================

ROOT = Path(__file__).resolve().parent.parent
BOOKS_JSON = ROOT / "data" / "books.json"


def main():
    if not BOOKS_JSON.exists():
        print(f"ERROR: books.json not found at {BOOKS_JSON}")
        return 1

    print(f"Reading {BOOKS_JSON}...")
    with open(BOOKS_JSON, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    slug = BOOK_ENTRY["id"]
    original_count = len(data["books"])

    # Remove any existing entry with this slug
    existing = [b for b in data["books"] if b["id"] == slug]
    if existing:
        print(f"  Removing {len(existing)} existing entry/entries with slug '{slug}'")
        data["books"] = [b for b in data["books"] if b["id"] != slug]

    # Insert new entry at the top (newest first)
    data["books"].insert(0, BOOK_ENTRY)

    # Update last_updated
    data["site"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")

    # Write back
    print(f"Writing {BOOKS_JSON}...")
    with open(BOOKS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    new_count = len(data["books"])
    print(f"\nDone. Total books: {original_count} -> {new_count}")
    print(f"Added/updated: {BOOK_ENTRY['title_ar']}")
    print(f"  English:  {BOOK_ENTRY['title_en']}")
    print(f"  Slug:     {slug}")
    print(f"  Category: {BOOK_ENTRY['category']}")

    # Verify the book files actually exist
    print("\nVerifying book files exist...")
    files_to_check = [
        ROOT / BOOK_ENTRY["cover"],
        *[ROOT / path for path in BOOK_ENTRY["files"].values()],
    ]
    all_exist = True
    for f in files_to_check:
        if f.exists():
            size = f.stat().st_size
            print(f"  [OK]   {f.relative_to(ROOT)} ({size:,} bytes)")
        else:
            print(f"  [MISSING] {f.relative_to(ROOT)}")
            all_exist = False

    if not all_exist:
        print("\nWARNING: Some files are missing.")
        print("Move them into the right folders before running git push.")
        print("  PDF/ePub/DOCX go in: assets/books/")
        print("  Cover image goes in: assets/covers/")
    else:
        print("\nAll files present. You can now run:")
        print("  cd C:\\Users\\FUJITSU-T902\\Downloads\\library")
        print("  git add .")
        print(f'  git commit -m "add: {slug} (externally produced)"')
        print("  git push")

    return 0


if __name__ == "__main__":
    sys.exit(main())
