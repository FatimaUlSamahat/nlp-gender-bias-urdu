"""Print the model's top-k guesses for every template, for a few names of each gender.
Usage:  python -m src.disco.inspect_preds --lang ur --model xlm-roberta-base
Shows whether the guesses are real words in the right script, or junk
(English words, punctuation, other languages). Also saves a JSON copy in results/.
"""
import json
import unicodedata
from argparse import ArgumentParser
from pathlib import Path

from transformers import pipeline
from transformers.utils import logging as hf_logging

from src.disco.data_io import load_names, load_templates

hf_logging.set_verbosity_error()

# Which Unicode script counts as "the right language" for each language code.
SCRIPT = {"ur": "ARABIC", "hi": "DEVANAGARI", "en": "LATIN"}
def in_script(token, script):
    """True if every letter in the token belongs to the expected script."""
    letters = [ch for ch in token if ch.isalpha()]
    return bool(letters) and all(script in unicodedata.name(ch, "") for ch in letters)
def main():
    ap = ArgumentParser()
    ap.add_argument("--lang", required=True)
    ap.add_argument("--model", default="xlm-roberta-base")
    ap.add_argument("--templates_dir", default="data/templates")
    ap.add_argument("--n_names", type=int, default=3, help="names per gender to show")
    ap.add_argument("--top_k", type=int, default=3)
    args = ap.parse_args()
    templates = load_templates(Path(args.templates_dir) / f"disco_templates_{args.lang}.json")
    names = load_names(args.lang).head(args.n_names)
    fill = pipeline("fill-mask", model=args.model, tokenizer=args.model)
    mask = fill.tokenizer.mask_token
    script = SCRIPT.get(args.lang)
    rows, good, total = [], 0, 0
    for i, (m_t, f_t) in enumerate(zip(templates["male"], templates["female"]), 1):
        t_good = t_total = 0
        print(f"\n=== Template {i}: {m_t}")
        for gender, template in (("male", m_t), ("female", f_t)):
            for name in names[gender]:
                sentence = template.replace("{PERSON}", name).replace("{BLANK}", mask)
                preds = fill(sentence, top_k=args.top_k)
                tokens = [p["token_str"].strip() for p in preds]
                ok = [in_script(t, script) for t in tokens] if script else [True] * len(tokens)
                t_good, t_total = t_good + sum(ok), t_total + len(ok)
                shown = ", ".join(f"{t}{'' if o else ' (x)'}" for t, o in zip(tokens, ok))
                print(f"  {gender:6s} {name:12s} -> {shown}")
                rows.append({"template": i, "gender": gender, "name": name, "tokens": tokens,
                             "probabilities": [float(p["score"]) for p in preds], "right_script": ok})
        print(f"  right script: {t_good}/{t_total}")
        good, total = good + t_good, total + t_total
    print(f"\nOVERALL: {good}/{total} guesses ({100 * good / total:.0f}%) are in the {script} script")
    print("(x) = not in the expected script: English, punctuation, other languages, or a word fragment")
    out = Path("results") / f"inspect_{args.lang}_{args.model.rstrip('/').split('/')[-1]}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"lang": args.lang, "model": args.model, "right_script_share": good / total,
                               "rows": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved: {out}")

if __name__ == "__main__":
    main()