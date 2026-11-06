# Gender bias across languages: English vs Urdu (CS 5316 NLP, Fall 2026)

Reproduces and extends Vashishtha, Ahuja, Sitaram (2023), "On Evaluating and Mitigating Gender Biases in
Multilingual Settings" (Findings of ACL), adding Urdu.

Members: Eshal Faisal, Laiba Naeem, Abeeha Imran, Fatima Ul Samahat.

## Layout
- `data/templates/`   DisCo templates (en = 14 from Webster et al. 2020; ur = ours)
- `data/names/`       gendered name lists
- `src/`              our code (copy from third_party/ then edit here)
- `third_party/`      authors' original code, unmodified, MIT licensed (we must disclose reuse)
- `results/`          small result files (JSON/CSV)
- `notebooks/`        exploration, one per person
- `report/`           report and slides
- `PLAN.md`           who does what and when; `CONTRIBUTING.md` git rules

## Setup
```
git clone <repo-url>
cd nlp-gender-bias-urdu
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
---

## Findings log

### 2026-11-06

#### Baseline DisCo scores (XLM-R base, no debiasing)

| Language | Templates | Names | DisCo score | Paper (Table 1) |
|---|---|---|---|---|
| English | 14 from Webster et al. (2020) | authors' list, 92+92 | 0.773 | 0.78 |
| Hindi | our own translation (not the authors') | authors' list, 164+164 | 0.897 | 0.83 (their templates) |
| Urdu v1 | direct translation (paper's method) | ours, 70+70 | 0.886 | not in paper |
| Urdu v2 | revised after inspection (frozen) | ours, 70+70 | 0.877 | not in paper |

Result files: `results/disco_<lang>_xlm-roberta-base[_v2].json`

#### Prediction inspection (`src/disco/inspect_preds.py`)
Top-3 guesses for every template, 3 male + 3 female names; share of guesses in the right script:

| English | Hindi | Urdu v1 | Urdu v2 |
|---|---|---|---|
| 87% (misses are mostly punctuation) | 100% | 81% | 93% |

- Urdu v1 problems were concentrated in a few templates: T1 ("is ___", Korean/English junk) and T8 ("never likes to ___", 0/18 Urdu, answered in Hindi script).
- XLM-R mixes Urdu with Hindi (Devanagari answers to Urdu prompts) and Persian spellings (گریه, فاطمه, من, می). Persian words count as "right script" but are not Urdu.
- Some templates attract filler words (کیا, یہ, بھی) instead of content words, mainly when the blank sits right before تھا. Blanks followed by کا/کی + noun work best.
- The names Ali and Hassan often produce word fragments (ا, ی, </s>) in the "likes to" templates.
- The authors' English templates have similar issues (T12/T14 get "This", "It").

#### Bias examples seen during inspection (3 names per gender, illustrative only)
- Urdu v2 T1 "is very ___": "sexy" (in English) predicted only for female names.
- Urdu T5-T7 "likes to ___": women → شادی (marriage), رقص (dancing), گریه (crying); men → ورزش (exercise), کام (work), بازی (games).
- Urdu v2 T8 "always avoids ___": women → شادی, محبت, نکاح, ازدواج.
- Hindi T7: women → पूजा, योग, प्रार्थना (worship, yoga, prayer).
- Content warning: several "likes to"/"never likes to" templates in all three languages produce sexual or violent words.

#### Same-gender control (`src/disco/control.py`, seed 0 only)
Score male-vs-male and female-vs-female with the same test. Gender effect = MF − average(MM, FF).

| Language | Name pairs | MF | MM | FF | Gender effect |
|---|---|---|---|---|---|
| Urdu | 35 | 0.902 | 0.878 | 0.874 | +0.027 |
| Hindi | 82 | 0.891 | 0.889 | 0.859 | +0.017 |
| English | 46 | 0.731 | 0.787 | 0.761 | −0.043 |

- Same-gender comparisons already score 0.79-0.89, so most of the DisCo score is name-to-name variation, not gender.
- Why: the authors' chi-square test gives p = 0 whenever a word appears in one top-3 list but not the other, so any difference in the top-3 counts as "biased".
- Improving the Urdu templates (81% → 93% valid predictions) changed the score by less than 0.01, which is consistent with this.
- Only one random split so far: needs seeds 1-4 before we rely on it (handed to Abeeha/Eshal). Debiasing results should also be run through the control.

#### Urdu templates v2 (`data/templates/v2/`, see its README)
- Rule: a template is acceptable if most top-3 guesses are real Urdu words of the intended kind; at most two revision rounds, then frozen.
- Changed T1, T4, T8, T11-T14. Gender-marked pairs: v1 = 4, v2 = 5.
- Still weak in v2: T13, T14 (filler words); T2, T3 (Hindi-script answers for female names).

#### Data issues found
- Authors' Hindi names: 2 duplicate male, 4 duplicate female, 6 names in both lists, some male names that are female names (and the reverse), first entry is the word for man/woman, stray spaces (we strip spaces).
- Authors' English names: one entry is "alice)" (kept for fidelity).
- Our Urdu names are mostly Muslim-associated, so they also signal religion.

#### Code changes
- `src/disco/data_io.py`: loads names from `data/names/<lang>_names.json` (needed for Urdu), validates data.
- `src/disco/check_data.py`: checks templates and names without a model.
- `src/disco/inspect_preds.py`: prints top-k guesses per template.
- `src/disco/control.py`: same-gender control.
- `run.py`: `--tag` option; harmless warnings silenced (scores unchanged, checked).
- `multilingual_disco.py`: authors' unused main() removed; optional names/templates override for the control. Original kept unmodified in `third_party/`.

#### Urdu CDA data (in progress, `src/cda/`)
Following the paper: English Wikipedia sentences → gender swap in English → machine-translate both into Urdu.
1. `data/cda/gender_pairs.tsv`: 75 male/female word pairs (paper: 193 from Lauscher et al. 2021). "host/hostess" removed (verb use).
2. `collect_sentences.py`: 10,000 English Wikipedia sentences, 8-40 words, with a Pakistan/South Asia keyword and a gendered word; shuffled reading order. Filters for "mother tongue", list entries, too-general keywords (hockey, cricket, mosque, sufi, ravi…).
3. `swap.py`: two-way swap of words + Pakistani name pairs matched by edit distance (paper's method); "her" → his/him decided by the next word. 9,972 pairs (28 sentences had nothing to swap). A sample of 10 was all correct.
4. `translate.py`: NLLB-200 distilled 600M, English → Urdu, ~2.2-2.5 pairs/s on Apple MPS. Running.
5. `check_sheet.py`: automatic checks + hand-check of 100 random pairs. To do.
- First 3 translated pairs: 2/3 flipped gender correctly; in 1 the translator kept the masculine verb (رہا).
- Most original sentences are about men (Wikipedia skew), which CDA balances.
- Names not in our list stay unchanged after swapping (e.g. a male name with "her"), as in the paper's method.

#### Deviations from the paper (to state in the report)
- Translator: NLLB instead of Bing.
- Keywords: our Pakistan/South Asia list instead of ConceptNet India keywords.
- 10,000 sentences instead of 20,000 (compute).
- 75 gender pairs instead of 193.
- Hindi templates and all Urdu data are our own.
- Library versions much newer than the authors' (torch 2.15, transformers 5.22); English score still matches (0.773 vs 0.78).

#### Open items
- Finish Urdu translation → hand-check 100 pairs → training file for Laiba.
- Second-speaker review of Urdu templates/names; Devanagari reader for Hindi templates; fill in `data/names/names_sources.md`.
- Control with seeds 1-4 (Abeeha/Eshal).
- mBERT and IndicBERT runs (Eshal).
