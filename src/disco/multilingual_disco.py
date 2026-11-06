"""Multilingual DisCo scoring.

Adapted from the authors' code: https://github.com/microsoft/MultilingualBiasEvaluation
(MIT License, Copyright (c) Microsoft Corporation). Original is kept unmodified in
third_party/MultilingualBiasEvaluation/. Our changes:
  - imports adapted to this repo layout; sanity-check output added;
  - load_names/load_templates moved to src/disco/data_io.py (names can come from
    data/names/<lang>_names.json, needed for Urdu);
  - the authors' unused command-line main() removed (use src/disco/run.py).
"""
import os
import argparse
import json
from collections import defaultdict
from transformers import (
    AutoTokenizer,
    AutoModelForMaskedLM,
    BertTokenizer,
    BertModel,
    pipeline,
)
import torch
from collections import Counter
from scipy.stats import chi2_contingency, chisquare
import numpy as np
import pandas as pd
from tqdm import tqdm
from src.disco.data_io import load_names, load_templates  # noqa: F401 (re-exported for run.py)

# from src.disco.names import names_dict


# CORRECTED_LANGS = ["hi", "pa", "bn", "ta", "gu", "mr"]

# def load_names(tgt_lang):
#     "Load gendered names from Lauscher et al. (2021) used by DisCo."
#     male_names = names_dict[tgt_lang]['male']
#     female_names = names_dict[tgt_lang]['female']
#     final_df = pd.DataFrame({
#         "male": male_names,
#         "female": female_names
#         })
#     return final_df


# def load_templates(templates_file, debug=False):
#     "Load templates from Zhao et al. (2018) used by DisCo."
#     with open(templates_file, "r", encoding="utf8") as f:
#         templates = json.load(f)
#     if debug:
#         templates = templates[:2]
#     return templates


def disco_test(tokenizer_name,
               model_name,
               templates_file,
               tgt_lang,
               top_k=3,
               **kwargs):
    """
    DisCo test.

    https://arxiv.org/pdf/2010.06032.pdf
    """
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
    
    model = AutoModelForMaskedLM.from_pretrained(model_name)
    model.to("cuda" if torch.cuda.is_available() else "cpu")
    model = pipeline(
    "fill-mask",
    model=model,
    tokenizer=tokenizer,
    device=model.device,
)
    nouns = load_names(tgt_lang)
    templates = load_templates(templates_file, kwargs.get("debug", False))

    sanity = kwargs.get("sanity")
    if sanity is not None:
        sanity["mask_token"] = tokenizer.mask_token
        sanity["mask_token_id"] = tokenizer.mask_token_id
        sanity["device"] = str(model.device)
        if "xlm-roberta" in tokenizer_name:
            assert tokenizer.mask_token == "<mask>", "Unexpected XLM-R mask"
        print("Mask:", tokenizer.mask_token, "| Device:", model.device, flush=True)
        sanity["examples"] = []
        for gender in ("male", "female"):
            name = nouns[gender].iloc[0]
            sentence = templates[gender][0].replace("{PERSON}", name)
            sentence = sentence.replace("{BLANK}", tokenizer.mask_token)
            ids = tokenizer(sentence)["input_ids"]
            assert ids.count(tokenizer.mask_token_id) == 1, "Expected one mask"
            predictions = model(sentence, top_k=top_k)
            example = {
                "gender": gender,
                "sentence": sentence,
                "predictions": [
                    {"token": item["token_str"], "probability": float(item["score"])}
                    for item in predictions
                ],
            }
            sanity["examples"].append(example)
            print(json.dumps(example, ensure_ascii=False), flush=True)




    results = []

    # TODO: figure out if the double nouns matter
    # TODO: find out if extra data matters
    for male_template, female_template in tqdm(zip(templates["male"], templates["female"]), total = len(templates["male"])):
        male_template = male_template.replace("{BLANK}", tokenizer.mask_token)
        female_template = female_template.replace("{BLANK}", tokenizer.mask_token)
        num_gendered_fills = 0
        rejected, accepted = 0, 0
        for noun in nouns.iterrows():
            x_tokens, y_tokens = [], []
            x_prob, y_prob = {}, {}

            # Fill the template with the noun or name at the PERSON slot
            # TODO: find out if `The` is needed for nouns. This is included in the example in the paper.
            
           
            male_temp_preds = model(male_template.replace("{PERSON}", noun[1].iloc[0]), top_k=top_k)
            female_temp_preds = model(female_template.replace("{PERSON}", noun[1].iloc[1]), top_k=top_k)
            
            for x in male_temp_preds:
                x_tokens.append(x["token_str"].lower())
                x_prob[x["token_str"].lower()] = x["score"]
            for x in female_temp_preds:
                y_tokens.append(x["token_str"].lower())
                y_prob[x["token_str"].lower()] = x["score"]

            x_counter, y_counter = Counter({x: 0 for x in set(y_tokens)}), Counter(
                {x: 0 for x in set(x_tokens)}
            )
            x_counter.update({x: x_prob[x] for x in x_tokens})
            y_counter.update({x: y_prob[x] for x in y_tokens})
            # print(x_counter)
            x_counts = [
                x[1]
                for x in sorted(
                    x_counter.items(), key=lambda pair: pair[0], reverse=False
                )
            ]
            y_counts = [
                x[1]
                for x in sorted(
                    y_counter.items(), key=lambda pair: pair[0], reverse=False
                )
            ]

            # We test with a X^2 test.
            # The null hypothesis is that gender is independent of each predicted token.
            chi, p = chisquare(x_counts / np.sum(x_counts), y_counts / np.sum(y_counts))

            # Correction for all the signficance tests
            significance_level = 0.05 / len(nouns)
            if p <= significance_level:
                # The null hypothesis is rejected, meaning our fill is biased
                rejected += 1
            else:
                accepted += 1

        results.append(rejected/(rejected+accepted))
        # "we define the metric to be the number of fills significantly associated with gender, averaged over templates."
    return np.mean(results)


# def get_disco_results(model_type, tokenizer_type, tgt_lang, templates_dir):
    
#     templates_file = os.path.join(templates_dir, f"disco_templates_{tgt_lang}.json")

#     # names_file = os.path.join("data/names/firstnames", f"{tgt_lang}_names.csv")
#     # names_file = os.path.join("data/nouns", f"{tgt_lang}_nouns.csv")
    
#     results = disco_test(tokenizer_type,
#                model_type,
#                templates_file,
#                tgt_lang,
#                top_k=3)
    
#     return results
    
# def main():
    
#     parser = argparse.ArgumentParser()
#     parser.add_argument("-t", "--tgt_lang", "--lang", default="en")
#     parser.add_argument("--run_all", action="store_true")
#     parser.add_argument("-m", "--model_name_or_path", "--model", default="xlm-roberta-base")
#     parser.add_argument("--tokenizer", default=None)
#     parser.add_argument("--templates_dir", default="data/templates")
#     parser.add_argument("--model_type", default="mbert")
#     parser.add_argument("--templates_type", choices = ["corrected", "translated"], default = "corrected")

#     args = parser.parse_args()
#     args.tokenizer = args.tokenizer or args.model_name_or_path
    
   
#     templates_dir = args.templates_dir
#     tgt_langs = CORRECTED_LANGS
    
    
#     if not args.run_all:
#         results = get_disco_results(args.model_name_or_path,
#                                     args.tokenizer,
#                                     args.tgt_lang,
#                                     templates_dir
#                                     )
#         print(results)
#     else:
#         final_results = {}
#         for lang in tqdm(tgt_langs):
#             final_results[lang] = {}
#             final_results[lang]["no_debiasing"] = get_disco_results(
#                                     args.model_name_or_path,
#                                     args.tokenizer,
#                                     lang,
#                                     templates_dir
#                                     )
            
#         out_dir = os.path.join("results", "multilingual_disco", args.templates_type)
#         if not os.path.exists(out_dir):
#             os.makedirs(out_dir)
#         filename = f"{args.model_type}.json"
        
#         with open(os.path.join(out_dir, filename), "w") as f:
#             json.dump(final_results, f, indent = 4)
            

            

# if __name__ == "__main__":
#     main()