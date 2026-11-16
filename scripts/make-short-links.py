# -*- coding: utf-8 -*-
"""
make-short-links.py — free, ad-free short links on your own site.

Creates one tiny redirect page per book:
    https://fadhlyemen.github.io/library/b/<number>/  ->  the book's PDF
Each page also carries the book's title, description and cover, so WhatsApp
and Facebook show the cover as a link preview.

Run from Command Prompt in the library folder:
    chcp 65001
    cd C:\\Users\\FUJITSU-T902\\Downloads\\library
    python make-short-links.py
    git add b data/short_ids.json
    git commit -m "own short links"
    git push

Run it again after every new book: existing numbers never change,
new books get the next number.
"""
import json, os, html, urllib.parse

SITE = "https://fadhlyemen.github.io/library/"
BOOKS = os.path.join("data", "books.json")
IDS = os.path.join("data", "short_ids.json")
OUT = "b"

# numbers 1..149 follow the WhatsApp posting order (day 1 = /b/1/)
SEED = {
 "end-of-universe-quran": 1,
 "glp1-blindness-naion": 2,
 "trust-in-america-islamic-inheritance": 3,
 "abdul-el-sayed": 4,
 "bosnia-herzegovina": 5,
 "drug-discovery-clinical-trials": 6,
 "my-grandmother-atiqa": 7,
 "healthcare-technology-ecosystem": 8,
 "halal-wealth-america": 9,
 "ilhan-omar": 10,
 "ali-abdullah-saleh": 11,
 "building-with-claude": 12,
 "fall-of-andalusia": 13,
 "start-company-america": 14,
 "ai-drug-discovery": 15,
 "trump-immigration-constitutional": 16,
 "captive-patient-healthcare": 17,
 "nvidia-throne-and-storm": 18,
 "yemeni-immigrant-guide": 19,
 "ai-education-planning-study": 20,
 "cupping-honey-cautery": 21,
 "macklemore-gaza": 22,
 "ai-strategic-planning-higher-ed": 23,
 "american-universities-secret": 24,
 "memory-loss-guide": 25,
 "art-of-parenting": 26,
 "nvidia-laptop-revolution": 27,
 "america-held-hostage": 28,
 "ust-sanaa-seizure": 29,
 "three-body-problem": 30,
 "tayyibat-diet-science": 31,
 "home-buying-america": 32,
 "ai-wave-spring-2026": 33,
 "saudi-succession": 34,
 "insurance-islam-guide": 35,
 "healthy-aging-guide": 36,
 "why-claude-excels": 37,
 "inheritance-comparative-law": 38,
 "build-store-site-lovable": 39,
 "political-ideologies-guide": 40,
 "bankruptcy-america": 41,
 "elite-ai-salaries": 42,
 "mastering-agentic-ai": 43,
 "us-hegemony-canada": 44,
 "art-of-persuasion": 45,
 "islamic-will-america": 46,
 "homosexuality-history-perspectives": 47,
 "yemen-epstein-files": 48,
 "claude-science-guide": 49,
 "claude-certification-exams": 50,
 "muslim-american-identity": 51,
 "tucker-carlson-gaza": 52,
 "statistical-genetics-encyclopedia": 53,
 "sunni-shia-rapprochement": 54,
 "yemen-brain-drain": 55,
 "muslim-nonmuslim-relations": 56,
 "statistical-genetics-guide": 57,
 "deep-state-america": 58,
 "ai-tools-arabic-knowledge-worker": 59,
 "generation-gap-diaspora": 60,
 "sufism-comprehensive-study": 61,
 "metabolonr-llm": 62,
 "us-midterms-2026-forecast": 63,
 "exercise-science-guide": 64,
 "ibrahim-al-hamdi-biography": 65,
 "youtube-challenges-guide": 66,
 "death-burial-america": 67,
 "claude-code-from-zero-to-deployed": 68,
 "john-kiriakou-whistleblower": 69,
 "food-health-hadith": 70,
 "google-deepmind": 71,
 "immigrant-loneliness-guide": 72,
 "quran-verses-classification": 73,
 "ml-algorithms-guide": 74,
 "gaza-siege-arab-abandonment": 75,
 "strategic-planning": 76,
 "muslim-marital-rights-west": 77,
 "divorce-america-islam": 78,
 "pos-accounting-guide": 79,
 "buddhism-hinduism-comparison": 80,
 "aipac-midterms-2026": 81,
 "attention-is-all-you-need": 82,
 "muslim-life-in-west": 83,
 "python-for-ai": 84,
 "yemen-saudi-relations": 85,
 "shisha-dangers-guide": 86,
 "cracking-consensus": 87,
 "arabic-nlp-and-the-llm": 88,
 "sins-ethics-religions": 89,
 "halal-mortgage-guide": 90,
 "ai-freelance-portfolio": 91,
 "journalists-killed-gaza": 92,
 "ai-content-creators": 93,
 "family-movies-guide": 94,
 "speak-like-native": 95,
 "massacres-against-muslims": 96,
 "no-code-ai-automation": 97,
 "campaign-finance-corruption": 98,
 "auto-mechanic-career-michigan": 99,
 "ai-agents-mcp": 100,
 "rag-engineering-guide": 101,
 "yemen-problems-history": 102,
 "tablighi-jamaat-study": 103,
 "best-us-cities-to-live": 104,
 "uae-israel-rapprochement": 105,
 "unhealthy-food-guide": 106,
 "ai-freelancing-guide": 107,
 "notebooklm-complete-guide": 108,
 "us-investment-visas-guide": 109,
 "obbba-impact-analysis": 110,
 "ai-jobs-future-2026-2036": 111,
 "usury-islamic-banking": 112,
 "supply-chain-guide": 113,
 "kidney-histology-reading-guide": 114,
 "us-tax-system-guide": 115,
 "gaza-stance-job-losses": 116,
 "quantum-mechanics-guide": 117,
 "halal-meat-michigan-indiana": 118,
 "quran-bible-comparative": 119,
 "ai-tools-guide": 120,
 "yemen-unity-ended": 121,
 "gaza-war-international-community": 122,
 "mythos-vs-anthropic": 123,
 "quran-scientific-miracles": 124,
 "coffee-world-guide": 125,
 "successful-marriage": 126,
 "generations-on-trial": 127,
 "claude-skills-guide": 128,
 "us-israel-convergence": 129,
 "signs-of-the-hour": 130,
 "data-engineering-guide": 131,
 "muslims-in-the-west": 132,
 "llm-research-education": 133,
 "us-israel-alliance-power": 134,
 "stock-market-investment-guide": 135,
 "cryptocurrencies": 136,
 "america-national-parks": 137,
 "islamic-caliphate-history": 138,
 "silicon-valley": 139,
 "yemen-presidents-wikileaks": 140,
 "legitimate-criticism-antisemitism": 141,
 "used-cars-america": 142,
 "claude-code-guide": 143,
 "retirement-planning": 144,
 "bioinformatics-future-ai": 145,
 "salafism-study": 146,
 "america-rise-decline": 147,
 "academic-success-us-universities": 148,
 "how-llms-work": 149,
 "prompt-engineering-llm4yemen": 150
}

def main():
    with open(BOOKS, encoding="utf-8-sig") as f:
        books = json.load(f)["books"]
    ids = dict(SEED)
    if os.path.exists(IDS):
        with open(IDS, encoding="utf-8-sig") as f:
            ids.update(json.load(f))
    nxt = max(ids.values(), default=0) + 1
    for b in books:
        if b["id"] not in ids:
            ids[b["id"]] = nxt
            print("new number", nxt, "->", b["id"])
            nxt += 1
    made = 0
    for b in books:
        n = ids[b["id"]]
        pdf = SITE + urllib.parse.quote(b["files"]["pdf"])
        cover = SITE + urllib.parse.quote(b.get("cover", "")) if b.get("cover") else ""
        title = b["title_ar"] + (" | " + b["title_en"] if b.get("title_en") else "")
        desc = (b.get("description_ar") or b.get("description_en") or "")[:200]
        e = lambda s: html.escape(s, quote=True)
        page = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl"><head><meta charset="utf-8">
<title>{e(title)}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta property="og:type" content="book">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{SITE}b/{n}/">
{f'<meta property="og:image" content="{e(cover)}">' if cover else ''}
<meta property="og:site_name" content="مكتبة فضل الأكوع الرقمية">
<meta http-equiv="refresh" content="0; url={e(pdf)}">
<link rel="canonical" href="{e(pdf)}">
<script>location.replace({json.dumps(pdf)});</script>
</head><body style="font-family:serif;text-align:center;padding:40px">
<p>جارٍ فتح الكتاب… · Opening the book…</p>
<p><a href="{e(pdf)}">اضغط هنا إن لم يُفتح · Tap here if it doesn't open</a></p>
</body></html>
"""
        d = os.path.join(OUT, str(n))
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write(page)
        made += 1
    with open(IDS, "w", encoding="utf-8") as f:
        json.dump(dict(sorted(ids.items(), key=lambda kv: kv[1])), f, ensure_ascii=False, indent=1)
    print("done:", made, "short links in", OUT + os.sep)

if __name__ == "__main__":
    main()
