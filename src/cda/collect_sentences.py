"""Step 2 of the Urdu CDA data: collect English Wikipedia sentences for counterfactual augmentation.

Follows Vashishtha et al. (2023): take English Wikipedia sentences with culture-related keywords
(they used India-related ConceptNet keywords; we use our own Pakistan/South Asia keyword list),
keep ones that contain a gendered word, stop at a target count.

Usage:  python -m src.cda.collect_sentences --target 20000
Output: data/cda/en_sentences.txt  (one sentence per line)
"""
import re
from argparse import ArgumentParser
from pathlib import Path

PAIRS_FILE = Path("data/cda/gender_pairs.tsv")

# Our replacement for the paper's ConceptNet India keywords: Pakistan / South Asia context.
KEYWORDS = """
pakistan pakistani lahore karachi islamabad rawalpindi peshawar quetta multan faisalabad hyderabad
sialkot gujranwala sindh punjab balochistan khyber pakhtunkhwa gilgit kashmir urdu punjabi sindhi pashto
saraiki balochi indus chenab jinnah iqbal lums ptv pti pml ppp eid ramadan ramzan nikah mehndi
biryani nihari karahi haleem qawwali ghazal shalwar kameez dupatta sherwani kurta lollywood dargah
""".split()


def load_gender_words(path=PAIRS_FILE):
    words = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            male, female = line.split("\t")
            words.update([male.strip(), female.strip()])
    return words


def split_sentences(text):
    """Simple sentence splitter: break after . ! ? followed by a space and a capital letter."""
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z])", text) if s.strip()]


# Gendered words that do not refer to a person: remove these phrases before looking for gendered words.
NOT_PERSON = re.compile(r"\bmother (tongues?|languages?|nature|country|ship)\b", re.IGNORECASE)
# Text-extraction glitches in the Wikipedia dump: words glued together ("invadedIndia", "with29,740", ",with").
GLUED = re.compile(r"[a-z]{2}[A-Z][a-z]|[a-z][0-9]|[,;][A-Za-z]")


def make_filter(gender_words, keywords=KEYWORDS, min_words=8, max_words=40):
    kw = re.compile(r"\b(" + "|".join(map(re.escape, keywords)) + r")\b", re.IGNORECASE)
    gw = re.compile(r"\b(" + "|".join(map(re.escape, sorted(gender_words))) + r")\b", re.IGNORECASE)

    def keep(sentence):
        n = len(sentence.split())
        return (min_words <= n <= max_words and "\n" not in sentence
                and sentence[0].isupper() and sentence.endswith((".", "!", "?"))
                and GLUED.search(sentence) is None
                and kw.search(sentence) is not None
                and gw.search(NOT_PERSON.sub("", sentence)) is not None)
    return keep


def main():
    ap = ArgumentParser()
    ap.add_argument("--target", type=int, default=20000, help="how many sentences to collect")
    ap.add_argument("--out", default="data/cda/en_sentences.txt")
    args = ap.parse_args()

    from datasets import load_dataset  # imported here so the helper functions work without it

    keep = make_filter(load_gender_words())
    wiki = load_dataset("wikimedia/wikipedia", "20231101.en", split="train", streaming=True)
    # Read files in a random order and mix articles, so we don't only get early "A" articles.
    wiki = wiki.shuffle(seed=0, buffer_size=10_000)
    seen, kept = set(), []
    for i, article in enumerate(wiki):
        for paragraph in article["text"].split("\n"):
            for s in split_sentences(paragraph):
                if keep(s) and s not in seen:
                    seen.add(s)
                    kept.append(s)
        if i % 5000 == 0:
            print(f"articles read: {i:,}  sentences kept: {len(kept):,}", flush=True)
        if len(kept) >= args.target:
            break
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(kept[:args.target]) + "\n", encoding="utf-8")
    print(f"Saved {min(len(kept), args.target):,} sentences to {out}")


if __name__ == "__main__":
    main()