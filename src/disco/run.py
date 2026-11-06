import os
os.environ.setdefault("LOGLEVEL", "ERROR")  # hides torch's harmless macOS "Redirects" noteimport os
import argparse
import hashlib
import json
import math
import platform
import subprocess
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

# from src.disco.multilingual_disco import disco_test, load_names, load_templates
from src.disco.data_io import load_names, load_templates, validate
from src.disco.multilingual_disco import disco_test
from transformers.utils import logging as hf_logging
hf_logging.set_verbosity_error()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", default="en")
    parser.add_argument("--model", default="xlm-roberta-base")
    parser.add_argument("--tokenizer", default=None)
    parser.add_argument("--templates_dir", default="data/templates")
    parser.add_argument("--templates_file", default=None)
    parser.add_argument("--tag", default="", help="added to the output file name, e.g. ext for the extended template set")
    args = parser.parse_args()

    tokenizer = args.tokenizer or args.model
    templates_path = (
        Path(args.templates_file) if args.templates_file
        else Path(args.templates_dir) / f"disco_templates_{args.lang}.json"
    )
    templates = load_templates(templates_path)
    names = load_names(args.lang)

    # assert len(templates["male"]) == len(templates["female"]) > 0
    # assert len(names) > 0 and not names.isna().any().any()
    # for gender in ("male", "female"):
    #     for template in templates[gender]:
    #         assert template.count("{PERSON}") == 1, template
    #         assert template.count("{BLANK}") == 1, template
    validate(templates, names)

    print(
        f"Running {len(templates['male'])} templates, "
        f"{len(names)} male + {len(names)} female names",
        flush=True,
    )

    sanity = {}
    score = float(disco_test(
        tokenizer, args.model, str(templates_path), args.lang,
        top_k=3, sanity=sanity,
    ))
    if not math.isfinite(score) or not 0 <= score <= 1:
        raise ValueError(f"Invalid score: {score}")

    packages = (
        "torch", "transformers", "tokenizers", "huggingface-hub",
        "scipy", "numpy", "pandas", "tqdm",
    )
    result = {
        "language": args.lang,
        "model": args.model,
        "tokenizer": tokenizer,
        "score": score,
        "number_of_templates": len(templates["male"]),
        "number_of_names": len(names) * 2,
        "names_per_gender": len(names),
        "date": datetime.now(timezone.utc).isoformat(),
        "top_k": 3,
        "debiasing": "none",
        "templates_file": templates_path.as_posix(),
        "templates_sha256": hashlib.sha256(templates_path.read_bytes()).hexdigest(),
        "python_version": platform.python_version(),
        "library_versions": {package: version(package) for package in packages},
        "sanity_check": sanity,
    }
    if args.lang == "en" and args.model == "xlm-roberta-base":
        result["paper_reported_score"] = 0.78
        result["difference_from_paper"] = score - 0.78
        result["paper_reference"] = (
            "Vashishtha et al. (2023), Table 1, XLM-R OOB, English"
        )

    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    model_label = args.model.rstrip("/").replace("\\", "/").split("/")[-1]
    suffix = f"_{args.tag}" if args.tag else ""
    output = output_dir / f"disco_{args.lang}_{model_label}{suffix}.json"
    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    frozen = subprocess.check_output(
        [sys.executable, "-m", "pip", "freeze"], text=True
    )
    (output_dir / f"disco_{args.lang}_{model_label}{suffix}_requirements.txt").write_text(
        frozen, encoding="utf-8"
    )
    print(f"\nDisCo score: {score:.6f}")
    print(f"Saved: {output}")
    if "difference_from_paper" in result:
        print(f"Paper: 0.78 | Difference: {score - 0.78:+.6f}")


if __name__ == "__main__":
    main()
