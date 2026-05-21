# Cowork Prompt — Wire Pre-Built MP3 → Library

**Reusable standing task for Dr. Fadhl Mohammed Alakwaa's library pipeline.**
Save this in Cowork as a named task. Each run, **attach the book's PDF
named `<slug>.pdf`** (the filename, minus `.pdf`, is the book's existing
`id` in `books.json`) OR just message the slug directly. Nothing else
needs to be typed.

---

## ARCHITECTURE — read this first

This task does NOT synthesize audio. The Cowork Linux sandbox cannot
reach `speech.platform.bing.com`, which is where edge-tts has to call.
Every attempt at synthesis here fails the same way at the proxy
allowlist, regardless of how the PDF is split or which fallback is tried.

**Synthesis happens on Fadhl's Windows machine via a single PowerShell
script: `scripts\Make-Audiobook.ps1` in the library repo.** It produces
`assets/books/<slug>.mp3` with correct ID3 tags, mono, ≤ 95 MB
(auto-fallback through 48 → 32 → 24 → 16 kbps if needed).

**This Cowork task does everything else:** slug resolution, MP3 sanity
checks, self-healing of `books.json`, sweeping all on-disk audiobooks
into the manifest, atomic commit, push, and verification.

The hard rule: if `assets/books/<slug>.mp3` does not exist, stop and
tell the user to run the PowerShell script. Do not split the PDF. Do
not call edge-tts. Do not probe the network. Do not "try anyway."

---

## INPUTS (each run)

```
(upload <slug>.pdf — OR just say the slug in your message)
```

**The PDF is the file uploaded to this task, not a path.** Do not ask
for a path. Locate the uploaded PDF yourself; its filename without
`.pdf` **is** `SLUG` (e.g. `signs-of-the-hour.pdf` →
`SLUG = signs-of-the-hour`). If more than one PDF is attached, use the
most recently uploaded one and state which you chose. If no PDF was
uploaded, parse `SLUG` from the user's text message.

The PDF itself is only used to derive the slug. Cowork does not need
the PDF for synthesis — the MP3 will already exist on disk by the time
this task runs.

Resolve titles automatically: open `data/books.json`, find the single
entry where `"id" == SLUG`, and take `TITLE_AR` from its `title_ar` and
`TITLE_EN` from its `title_en`. **Do not type or guess titles.**

If no entry has `"id" == SLUG`, **stop** and report the mismatch (likely
a filename typo) — do NOT invent a slug or create a new library entry.
The audiobook only ever attaches to a book that already exists.

---

## STEPS (fixed recipe — follow exactly)

### 1. Resolve slug, look up titles

Derive `SLUG` from the upload filename or user message. Find the entry
in `data/books.json` where `"id" == SLUG`:

```bash
python3 << 'PY'
import json
with open('data/books.json', encoding='utf-8-sig') as f:
    data = json.load(f)
slug = '<SLUG>'
book = next((b for b in data['books'] if b['id'] == slug), None)
if not book:
    raise SystemExit(f'Slug {slug!r} not in books.json — likely a filename typo')
print('TITLE_AR:', book['title_ar'])
print('TITLE_EN:', book['title_en'])
PY
```

If found, capture `TITLE_AR` and `TITLE_EN`. If not, stop.

### 2. Precondition check — the MP3 must already exist

```bash
test -f assets/books/<SLUG>.mp3 && stat -c '%s' assets/books/<SLUG>.mp3
```

**If the file does not exist or is empty:** STOP IMMEDIATELY and output
exactly this to the user, then exit. Make no changes:

```
The audiobook hasn't been synthesized yet. Run this in PowerShell on
your Windows machine:

    cd C:\Users\FUJITSU-T902\Downloads\library
    Set-ExecutionPolicy -Scope Process Bypass -Force
    .\scripts\Make-Audiobook.ps1 -Slug "<SLUG>"

Wait for it to finish (5–60 min depending on book length), then
re-invoke this task to do the wiring and push.
```

Do not edit `books.json`. Do not commit anything. Do not split the
PDF. Do not run any preparation step.

### 3. Verify MP3 sanity

The file exists. Verify it's actually usable:

```bash
SIZE=$(stat -c '%s' assets/books/<SLUG>.mp3)
echo "Size: $(echo "scale=1; $SIZE / 1024 / 1024" | bc) MB"
[ "$SIZE" -lt 99614720 ] || { echo "ERROR: file >95MB"; exit 1; }

# Must be parseable + must have title and artist
ffprobe -v error -show_entries format=duration,bit_rate \
        -show_entries format_tags=title,artist \
        -of default=noprint_wrappers=1 assets/books/<SLUG>.mp3
```

If size > 95 MB, ID3 tags missing, or ffprobe errors: tell the user
exactly what failed and stop. Fixes happen via `Make-Audiobook.ps1 -Force`,
not here.

### 4. Self-heal `data/books.json` if it is broken

Try to parse. If it fails to parse or `books[]` has fewer than 105
entries (the known-good floor), recover from the most recent good commit:

```bash
python3 -c "
import json
d = json.load(open('data/books.json', encoding='utf-8-sig'))
assert isinstance(d.get('books'), list) and len(d['books']) >= 105
" 2>/dev/null || {
  echo "Manifest broken — recovering from history"
  for sha in $(git log --format=%H -- data/books.json | head -50); do
    if git show "$sha:data/books.json" | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert isinstance(d.get('books'), list) and len(d['books']) >= 105
" 2>/dev/null; then
      echo "Recovered from $sha"
      git show "$sha:data/books.json" > data/books.json
      break
    fi
  done
}
```

### 5. Reconcile ALL on-disk audiobooks into the manifest (safety net)

Do not trust the manifest to already list every audiobook. Sweep
`assets/books/*.mp3` and reconcile every one — this guarantees no prior
audio wiring is silently dropped, even if a past run left the manifest
in a partial state.

```bash
python3 << 'PY'
import json, os, tempfile
from pathlib import Path
from datetime import date

with open('data/books.json', encoding='utf-8-sig') as f:
    data = json.load(f)

mp3_files = {p.stem: p for p in Path('assets/books').glob('*.mp3')}
known_ids = {b['id'] for b in data['books']}

reconciled, orphans = [], []
for slug in sorted(mp3_files):
    if slug not in known_ids:
        orphans.append(slug)
        continue
    book = next(b for b in data['books'] if b['id'] == slug)
    relpath = f'assets/books/{slug}.mp3'
    files = book.setdefault('files', {})
    formats = book.setdefault('formats', [])
    changed = False
    if files.get('mp3') != relpath:
        files['mp3'] = relpath
        changed = True
    if 'mp3' not in formats:
        formats.append('mp3')
        changed = True
    if changed:
        reconciled.append(slug)

data.setdefault('site', {})['last_updated'] = date.today().isoformat()

# Atomic write — temp file + replace, never partial JSON to books.json
fd, tmp = tempfile.mkstemp(dir='data', suffix='.json.tmp')
with os.fdopen(fd, 'w', encoding='utf-8', newline='\r\n') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
os.replace(tmp, 'data/books.json')

print(f'Reconciled: {reconciled or "no changes needed"}')
if orphans:
    print(f'WARNING: MP3 on disk with no books.json entry: {orphans}')
PY
```

CRLF line endings, 2-space indent, raw UTF-8 Arabic (`ensure_ascii=False`)
— preserved by the writer above.

### 6. Validate the written manifest before committing

```bash
# Must parse
python3 -c "import json; json.load(open('data/books.json', encoding='utf-8-sig'))" \
  || { echo "PARSE FAIL — aborting"; git checkout HEAD -- data/books.json; exit 1; }

# Book count must not have regressed
python3 << 'PY' || { echo "COUNT REGRESS — aborting"; git checkout HEAD -- data/books.json; exit 1; }
import json, subprocess
new = len(json.load(open('data/books.json', encoding='utf-8-sig'))['books'])
head = subprocess.check_output(['git', 'show', 'HEAD:data/books.json']).decode('utf-8-sig')
old = len(json.loads(head)['books'])
print(f'Book count: HEAD={old}, new={new}')
assert new >= old, f'REGRESS: {old} -> {new}'
PY
```

If either guard fails, the manifest is restored from HEAD via the
`git checkout` in the failure branch, and the task aborts. Do NOT push.

### 7. Commit and push

```bash
git add assets/books/<SLUG>.mp3 data/books.json
git commit -m "Add audio edition for <SLUG>"
git push origin main
```

If `git push` fails (auth, conflict, large file), report exactly what
happened and stop. Do not force-push. Do not rebase.

### 8. Verify Pages serves it

```bash
sleep 60
curl -sI "https://fadhlyemen.github.io/library/assets/books/<SLUG>.mp3" | head -1
```

Expect `HTTP/2 200`. If 404, wait another 60s and retry once. Report
the final status; don't loop indefinitely.

### 9. Report

Output:
- `SLUG`, `TITLE_AR`, final size, duration, bitrate (from ffprobe)
- Commit SHA (`git rev-parse HEAD`)
- Pages URL
- Anything reconciled beyond this slug — e.g. "also re-wired N other
  existing audiobooks that were missing manifest entries"

---

## GUARDRAILS

- ✅ Synthesis lives in PowerShell (`Make-Audiobook.ps1`), never here.
- ✅ If MP3 missing → output the PowerShell command and STOP. No splitting, no probing, no fallback.
- ✅ Always sweep ALL `assets/books/*.mp3` — never rely on the manifest alone.
- ✅ Atomic writes only (temp file + `os.replace`).
- ✅ Validate parse + book count BEFORE commit, every time.
- ✅ Final repo MP3 ≤ 95 MB (enforced by `Make-Audiobook.ps1`; verified here).
- ✅ Attach to the **existing** slug — never mint a new library entry.
- ✅ Audio wired ONLY via `books.json` (`files.mp3` + `formats`).
- ✅ Preserve CRLF line endings, 2-space indent, raw UTF-8 Arabic in `books.json`.
- ✅ Author: **د. فضل محمد الأكوع / Dr. Fadhl Mohammed Alakwaa** (never "Al-Akwa'a").
- ❌ Never call `edge-tts`. Never run `book_to_audiobook.py`. Never probe `speech.platform.bing.com`.
- ❌ Never commit a `books.json` that doesn't parse.
- ❌ Never reduce the book count vs. `HEAD`.
- ❌ Never let PowerShell write to `books.json` directly (encoding corrupts Arabic).
- ❌ Never run `produce-book.py` (PDF-only, never add audio logic to it).
- ❌ Never modify another book entry, the PDF/EPUB/DOCX, or covers.
- ❌ Never force-push, rebase, or rewrite history.

---

## If the MP3 is > 95 MB even after `Make-Audiobook.ps1` auto-fallback

(Extremely long books only — typically > 8 hours.) The script will
have thrown `Couldn't fit under 95 MB even at 16 kbps`. In that case
the MP3 is not in `assets/books/`. Tell the user to attach the file
to a **GitHub Release** (2 GB limit per asset) and report the release
asset URL so it can be linked from the library instead of committed
to the repo. Do not commit a > 100 MB file.
