"""Same-gender control for DisCo.

Question: if we compare two groups of the SAME gender, how high is the DisCo score?
If male-vs-male is about as high as male-vs-female, the score mostly measures
name-to-name noise, not gender.

Three runs, all with the same number of name pairs so they are comparable:
  MF: male names (group A)   vs female names (group A)   <- the normal test, smaller
  MM: male names (group A)   vs male names (group B)     <- control, male template both sides
  FF: female names (group A) vs female names (group B)   <- control, female template both sides

Usage:  python -m src.disco.control --lang ur --model xlm-roberta-base
"""
import json
import random
from argparse import ArgumentParser
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from transformers.utils import logging as hf_logging

from src.disco.data_io import load_names, load_templates, validate
from src.disco.multilingual_disco import disco_test

hf_logging.set_verbosity_error()


def main():
    ap = ArgumentParser()
    ap.add_argument("--lang", required=True)
    ap.add_argument("--model", default="xlm-roberta-base")
    ap.add_argument("--templates_dir", default="data/templates")
    ap.add_argument("--seed", type=int, default=0, help="fixes the random split so runs are repeatable")
    args = ap.parse_args()

    path = Path(args.templates_dir) / f"disco_templates_{args.lang}.json"
    templates, names = load_templates(path), load_names(args.lang)
    validate(templates, names)

    # Shuffle each gender's names with a fixed seed, then split into two equal halves A and B.
    rng = random.Random(args.seed)
    male, female = list(names["male"]), list(names["female"])
    rng.shuffle(male)
    rng.shuffle(female)
    half = len(male) // 2
    m_a, m_b, f_a, f_b = male[:half], male[half:2 * half], female[:half], female[half:2 * half]

    # Each run: "male" column goes into the first template list, "female" column into the second.
    runs = {
        "MF": (pd.DataFrame({"male": m_a, "female": f_a}), templates),
        "MM": (pd.DataFrame({"male": m_a, "female": m_b}), {"male": templates["male"], "female": templates["male"]}),
        "FF": (pd.DataFrame({"male": f_a, "female": f_b}), {"male": templates["female"], "female": templates["female"]}),
    }

    scores = {}
    for label, (nouns, tmpl) in runs.items():
        print(f"\n--- {label}: {len(nouns)} name pairs ---", flush=True)
        scores[label] = float(disco_test(args.model, args.model, str(path), args.lang,
                                         top_k=3, nouns=nouns, templates=tmpl))
        print(f"{label} score: {scores[label]:.4f}", flush=True)

    same = (scores["MM"] + scores["FF"]) / 2
    gender_effect = scores["MF"] - same
    print(f"\nMF (male vs female): {scores['MF']:.4f}")
    print(f"MM (male vs male):   {scores['MM']:.4f}")
    print(f"FF (female vs female): {scores['FF']:.4f}")
    print(f"Gender effect = MF - average(MM, FF) = {gender_effect:+.4f}")

    out = Path("results") / f"control_{args.lang}_{args.model.rstrip('/').split('/')[-1]}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({
        "language": args.lang, "model": args.model, "seed": args.seed,
        "name_pairs_per_run": half, "scores": scores,
        "same_gender_average": same, "gender_effect": gender_effect,
        "templates_file": path.as_posix(), "date": datetime.now(timezone.utc).isoformat(),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()