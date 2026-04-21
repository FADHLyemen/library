# مكتبة د. فضل الأكوع — Dr. Fadhl Alakwaa Library

A static, data-driven digital library for Dr. Fadhl Mohammed Alakwaa's books.  
**Single source of truth:** `data/books.json`. Everything else on the site renders from that one file.

Live site: **https://fadhlyemen.github.io/library/**

---

## Philosophy: minimal involvement

This repo is built around one principle — **adding a new book should be one command, not a web project**. The site's HTML and CSS are finished. You will not need to edit them ever again. Each new book is:

1. Produced in a Claude conversation (PDF + ePub + DOCX + cover).
2. Handed to `scripts/publish.py`, which copies the files in, updates `books.json`, commits, and pushes.
3. GitHub Pages auto-rebuilds the live site in ~60 seconds.

The Salman al-Awda book is hard-excluded at two levels (the `publish.py` allow-list and the JavaScript loader), so it cannot accidentally appear.

---

## Repo layout

```
library/
├── index.html                 ← the homepage (you never edit this)
├── css/style.css              ← design system (you never edit this)
├── js/main.js                 ← manifest loader + UI logic (you never edit this)
├── data/
│   └── books.json             ← the one file that controls everything
├── assets/
│   ├── fonts/                 ← self-hosted Amiri (Regular, Bold, Italic, Quran)
│   ├── covers/                ← book cover thumbnails (JPG, ~400×560)
│   └── books/                 ← PDF, ePub, DOCX download files
├── scripts/
│   ├── publish.py             ← one-command book publisher
│   └── generate_placeholder_covers.py
├── .github/workflows/
│   └── deploy.yml             ← (optional) GitHub Actions auto-deploy
├── .gitignore
└── README.md
```

---

## First-time setup

### 1. Clone (or replace your existing library folder)

If you already have `fadhlyemen/library/` on GitHub, back it up, then drop these files in and push. If you're starting fresh:

```bash
git clone https://github.com/fadhlyemen/library.git
cd library
# copy all files from this package into the repo
git add .
git commit -m "rebuild: data-driven library architecture"
git push origin main
```

### 2. Enable GitHub Pages (if not already enabled)

GitHub repo → Settings → Pages → Source: *Deploy from a branch* → Branch: `main` / folder: `/ (root)`.

Within ~60 seconds the site is live at `https://fadhlyemen.github.io/library/`.

### 3. Upload your real book files

The repo ships with **31 placeholder covers** (auto-generated, navy + gold with Amiri titles) but no PDF/ePub/DOCX files yet. To upload real book files:

- Drop them into `assets/books/` with filenames matching each book's `id` in `books.json`.  
  Example: book id `how-llms-work` → files `assets/books/how-llms-work.pdf`, `.epub`, `.docx`.
- Drop real cover images into `assets/covers/<id>.jpg`. Recommended 800×1120.
- Commit + push. The site updates automatically.

Or — preferred workflow — use `publish.py` which does all of this in one step.

---

## Adding a new book (the 30-second workflow)

After Claude produces a book and places the outputs in `/mnt/user-data/outputs/`:

```bash
python scripts/publish.py \
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
    --description-en "A simplified explanation of how LLMs work..."
```

Or run it with no arguments and it will prompt you for each field interactively:

```bash
python scripts/publish.py
```

The script:
1. Copies files into `assets/books/` and `assets/covers/`
2. Resizes the cover to 800px wide (so the site loads fast)
3. Appends or updates the entry in `data/books.json`
4. Runs `git add`, `git commit`, `git push`
5. Prints confirmation

Your live site now shows the new book within a minute.

### Available categories
`quran`, `islamic`, `yemen`, `politics`, `tech`, `family`, `diaspora`, `personal`

---

## Customizing

You **can** edit the site — you just rarely need to. Common edits:

### Change the masthead tagline
Edit `index.html`, search for `library-tagline`, change the `data-ar` and `data-en` attributes.

### Add a new category
1. Add an entry to the `categories` array in `data/books.json`.
2. Add the category ID to `VALID_CATEGORIES` in `scripts/publish.py`.

### Change the palette
Edit `css/style.css` top block — `--gold`, `--navy`, `--cream` are defined as CSS variables once and used everywhere.

### Feature a book
Set `"featured": true` in its `books.json` entry. Up to 4 featured books are shown in the "مختارات المكتبة" spotlight section at the top.

### Mark a book as in-production
Set `"status": "in-production"` in its entry. A gold "قيد الإعداد / In production" badge appears on the card.

---

## Running locally

To preview changes before pushing:

```bash
cd library
python3 -m http.server 8000
# open http://localhost:8000 in your browser
```

---

## Optional: Automated deployment via GitHub Actions

The repo includes `.github/workflows/deploy.yml` — if you enable it, GitHub Pages will redeploy via Actions (which is slightly faster and lets you run pre-deploy scripts like RSS feed generation later). For basic setups this is not needed; the default branch-based Pages deploy works fine.

---

## Browser support

Modern evergreen browsers (Chrome, Safari, Firefox, Edge) from 2021+.  
Uses: CSS Grid, `<dialog>`, `fetch()`, ES2020 JavaScript.

---

## Fonts

Self-hosted from the [aliftype/amiri](https://github.com/aliftype/amiri) v1.000 release, distributed under [SIL Open Font License](assets/fonts/OFL.txt).

---

## License

Site code: author retains all rights. Book content: © Dr. Fadhl Mohammed Alakwaa.  
See `assets/fonts/OFL.txt` for the Amiri font license.

---

## Questions / issues

Open an issue on GitHub or contact Dr. Alakwaa directly.
