"""Step 3 of the CDA data: make the gender-swapped (counterfactual) copy of each English sentence.

Follows Vashishtha et al. (2023): word replacement with gendered term pairs, plus male<->female
personal-name pairs matched by minimum edit distance (they did this for Indian names; we use
Pakistani names). Swaps go both ways: he->she and she->he in the same pass.

Usage:  python -m src.cda.swap --inp data/cda/en_sentences.txt --out data/cda/en_pairs.jsonl
Output: one JSON object per line: {"id", "en", "en_cf", "n_swaps"}
"""
import json
import re
from argparse import ArgumentParser
from pathlib import Path

PAIRS_FILE = Path("data/cda/gender_pairs.tsv")

# Romanised versions of our Urdu name lists (data/names/ur_names.json), same order.
MALE_NAMES = """Ahmed Ali Hassan Hussain Umar Usman Bilal Hamza Zain Fahad Faisal Kamran Imran Salman Arshad
Asad Ashraf Akram Asif Atif Abid Adnan Irfan Farhan Fawad Haris Haider Hashim Ibrahim Ismail Azhar Javed
Jamshed Khalid Khurram Danish Zeeshan Rashid Rizwan Sajid Saad Shahid Shahzad Shoaib Sabir Tariq Talha
Zafar Aamir Abbas Abdullah Atiq Farooq Qasim Kashif Luqman Mubashir Mohsin Mustafa Muaz Munir Nasir Noman
Naveed Waseem Waqar Waleed Yasir Yousuf Younis""".split()
FEMALE_NAMES = """Ayesha Fatima Zainab Maryam Khadija Amna Sara Saadia Nadia Sana Saba Saima Rukhsana Shabana
Shazia Nasreen Nazia Naila Uzma Ammara Iffat Fouzia Farzana Fariha Faiza Kanwal Komal Mehwish Mehak Madiha
Mehreen Maria Nimra Neelam Nabila Naheed Rabia Rubab Razia Robina Rimsha Rehana Sumaira Sumbul Sidra Salma
Sehar Shaista Shagufta Shireen Shakila Safia Tayyaba Aliya Urooj Arooba Azra Ghazala Lubna Maira Mubarika
Mishal Nargis Nusrat Hania Hajra Yasmin Bushra Batool Sameena""".split()

# After "her", these words mean "her" is an object ("saw her at", "told her that") -> "him".
# Anything else after "her" is treated as possessive ("her father") -> "his".
HER_OBJECT_NEXT = set("""to and in at for with from as on by that the a an of or but when after before
while if than into about over under until because so this these those it its he she they his him her
was is were are had has have be been who which during through against without""".split())


def edit_distance(a, b):
    a, b = a.lower(), b.lower()
    row = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        prev, row[0] = row[0], i
        for j, cb in enumerate(b, 1):
            prev, row[j] = row[j], min(row[j] + 1, row[j - 1] + 1, prev + (ca != cb))
    return row[-1]


def name_pairs(male=MALE_NAMES, female=FEMALE_NAMES):
    """Greedy matching: repeatedly pair the closest (male, female) names by edit distance."""
    candidates = sorted((edit_distance(m, f), m, f) for m in male for f in female)
    used_m, used_f, pairs = set(), set(), []
    for _, m, f in candidates:
        if m not in used_m and f not in used_f:
            pairs.append((m, f))
            used_m.add(m)
            used_f.add(f)
    return pairs


def load_mapping(path=PAIRS_FILE):
    """Build a two-way word map. 'her' is left out: it is decided by context in swap()."""
    mapping = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            male, female = (w.strip().lower() for w in line.split("\t"))
            mapping[male] = female
            if female != "her":
                mapping[female] = male
    for m, f in name_pairs():
        mapping[m.lower()] = f.lower()
        mapping[f.lower()] = m.lower()
    return mapping


def match_case(new, old):
    if old.isupper() and len(old) > 1:
        return new.upper()
    if old[0].isupper():
        return new[0].upper() + new[1:]
    return new


def make_swapper(mapping):
    words = sorted(set(mapping) | {"her"}, key=len, reverse=True)
    pattern = re.compile(r"\b(" + "|".join(map(re.escape, words)) + r")\b", re.IGNORECASE)

    def swap(sentence):
        count = 0

        def repl(m):
            nonlocal count
            word = m.group(0)
            low = word.lower()
            if low == "her":
                nxt = re.match(r"\s*([A-Za-z]+)", sentence[m.end():])
                new = "him" if (nxt is None or nxt.group(1).lower() in HER_OBJECT_NEXT) else "his"
            else:
                new = mapping[low]
            count += 1
            return match_case(new, word)

        return pattern.sub(repl, sentence), count
    return swap


def main():
    ap = ArgumentParser()
    ap.add_argument("--inp", default="data/cda/en_sentences.txt")
    ap.add_argument("--out", default="data/cda/en_pairs.jsonl")
    args = ap.parse_args()

    swap = make_swapper(load_mapping())
    sentences = [s for s in Path(args.inp).read_text(encoding="utf-8").splitlines() if s.strip()]
    rows, skipped = [], 0
    for i, s in enumerate(sentences):
        cf, n = swap(s)
        if n == 0:
            skipped += 1
            continue
        rows.append({"id": i, "en": s, "en_cf": cf, "n_swaps": n})
    out = Path(args.out)
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print(f"{len(rows):,} pairs saved to {out} ({skipped} sentences had nothing to swap)")
    for r in rows[:5]:
        print(f"\n  {r['en']}\n  {r['en_cf']}")


if __name__ == "__main__":
    main()