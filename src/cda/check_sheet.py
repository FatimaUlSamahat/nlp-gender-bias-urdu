"""Step 5 of the CDA data: quality checks on the translated pairs.

  make : automatic checks on ALL pairs + a CSV of 100 random pairs for you to mark by hand
         python -m src.cda.check_sheet make --lang ur
  score: after you have filled in the CSV, count the results
         python -m src.cda.check_sheet score --lang ur

Columns to fill in the CSV (write y or n):
    gender_flipped  : y = flipped correctly, n = should have flipped but didn't, na = Urdu sentence can't show gender
  translation_ok  : are both Urdu sentences understandable translations of the English?
"""
import csv
import json
import random
from argparse import ArgumentParser
from pathlib import Path


def load(lang):
    path = Path(f"data/cda/pairs_{lang}.jsonl")
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def make(lang, n, seed):
    rows = load(lang)
    identical = [r for r in rows if r[lang].strip() == r[f"{lang}_cf"].strip()]
    empty = [r for r in rows if not r[lang].strip() or not r[f"{lang}_cf"].strip()]
    latin = [r for r in rows if sum(c.isascii() and c.isalpha() for c in r[lang]) > len(r[lang]) * 0.3]
    print(f"pairs translated: {len(rows):,}")
    print(f"Urdu original and swapped IDENTICAL (gender change lost): {len(identical):,} "
          f"({100 * len(identical) / len(rows):.1f}%)")
    print(f"empty translations: {len(empty):,}")
    print(f"mostly Latin letters (translation probably failed): {len(latin):,}")

    sample = random.Random(seed).sample(rows, min(n, len(rows)))
    out = Path(f"data/cda/check_{lang}.csv")
    # utf-8-sig adds a marker so Excel/Numbers show Urdu correctly
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "en", "en_cf", lang, f"{lang}_cf", "gender_flipped", "translation_ok", "notes"])
        for r in sample:
            w.writerow([r["id"], r["en"], r["en_cf"], r[lang], r[f"{lang}_cf"], "", "", ""])
    print(f"\nWrote {len(sample)} random pairs to {out}: fill in gender_flipped and translation_ok with y/n")


def score(lang):
    path = Path(f"data/cda/check_{lang}.csv")
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    g = [r["gender_flipped"].strip().lower() for r in rows]
    y, n, na = g.count("y"), g.count("n"), g.count("na")
    print(f"gender_flipped: {y} y, {n} n, {na} na (gender not visible in Urdu), "
          f"{len(rows) - y - n - na} not marked")
    print(f"  error rate where gender should be visible: {n}/{y + n} ({100 * n / max(y + n, 1):.0f}%)")
    t = [r["translation_ok"].strip().lower() for r in rows]
    print(f"translation_ok: {t.count('y')}/{t.count('y') + t.count('n')} yes "
          f"({100 * t.count('y') / max(t.count('y') + t.count('n'), 1):.0f}%)")

def main():
    ap = ArgumentParser()
    ap.add_argument("action", choices=["make", "score"])
    ap.add_argument("--lang", default="ur")
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    make(args.lang, args.n, args.seed) if args.action == "make" else score(args.lang)


if __name__ == "__main__":
    main()