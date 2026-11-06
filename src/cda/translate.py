"""Step 4 of the CDA data: translate each English original + swapped sentence into Urdu or Hindi.

The paper used the Bing translator; we use the open NLLB model (facebook/nllb-200-distilled-600M).
Translating AFTER swapping in English lets the translator produce correct gendered verbs
(e.g. kiya/ki, karta/karti) that simple word replacement in Urdu would get wrong.

Usage:  python -m src.cda.translate --lang ur --limit 100     (small timing test first)
        python -m src.cda.translate --lang ur                 (everything; can be stopped and resumed)
Output: data/cda/pairs_<lang>.jsonl with {"id", "en", "en_cf", "<lang>", "<lang>_cf"}
"""
import json
import time
from argparse import ArgumentParser
from pathlib import Path

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from transformers.utils import logging as hf_logging

hf_logging.set_verbosity_error()

MODEL = "facebook/nllb-200-distilled-600M"
NLLB_CODES = {"ur": "urd_Arab", "hi": "hin_Deva"}


def pick_device():
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():  # Apple Silicon GPU
        return "mps"
    return "cpu"


def main():
    ap = ArgumentParser()
    ap.add_argument("--lang", required=True, choices=sorted(NLLB_CODES))
    ap.add_argument("--inp", default="data/cda/en_pairs.jsonl")
    ap.add_argument("--limit", type=int, default=None, help="only the first N pairs (for a timing test)")
    ap.add_argument("--batch", type=int, default=16, help="pairs per batch (2x sentences)")
    ap.add_argument("--beams", type=int, default=2, help="beam search width: higher = better but slower")
    args = ap.parse_args()

    out = Path(f"data/cda/pairs_{args.lang}.jsonl")
    done = set()
    if out.exists():  # resume: skip pairs already translated
        done = {json.loads(line)["id"] for line in out.read_text(encoding="utf-8").splitlines() if line}
    rows = [json.loads(line) for line in Path(args.inp).read_text(encoding="utf-8").splitlines() if line]
    if args.limit:
        rows = rows[:args.limit]
    todo = [r for r in rows if r["id"] not in done]
    print(f"{len(done):,} already done, {len(todo):,} to translate into {args.lang}", flush=True)
    if not todo:
        return

    device = pick_device()
    tok = AutoTokenizer.from_pretrained(MODEL, src_lang="eng_Latn")
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL).to(device).eval()
    target_id = tok.convert_tokens_to_ids(NLLB_CODES[args.lang])
    print(f"device: {device}", flush=True)

    start = time.time()
    with open(out, "a", encoding="utf-8") as f:
        for b in range(0, len(todo), args.batch):
            batch = todo[b:b + args.batch]
            texts = [r["en"] for r in batch] + [r["en_cf"] for r in batch]
            enc = tok(texts, return_tensors="pt", padding=True, truncation=True, max_length=128).to(device)
            with torch.no_grad():
                gen = model.generate(**enc, forced_bos_token_id=target_id,
                                     num_beams=args.beams, max_new_tokens=160)
            outs = tok.batch_decode(gen, skip_special_tokens=True)
            n = len(batch)
            for r, orig, cf in zip(batch, outs[:n], outs[n:]):
                row = {"id": r["id"], "en": r["en"], "en_cf": r["en_cf"], args.lang: orig, f"{args.lang}_cf": cf}
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            done_now = b + n
            rate = done_now / (time.time() - start)
            left = (len(todo) - done_now) / rate / 60
            print(f"{done_now:,}/{len(todo):,} pairs  ({rate:.1f} pairs/s, ~{left:.0f} min left)", flush=True)
    print(f"Saved to {out}")


if __name__ == "__main__":
    main()