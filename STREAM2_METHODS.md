# Stream 2: CDA and Self-Debiasing

## Methods
- Base model: XLM-RoBERTa-base
- CDA variants: English, Urdu, English+Urdu, Hindi, and Hindi+Urdu
- Evaluation: DisCo on English and Urdu templates
- Same-gender controls: MF, MM, FF across five seeds
- Self-Debiasing: experimental inference-time adaptation

## Results
- results/stream2_cda_retrained.json: latest CDA DisCo scores
- results/stream2_final_comparison.csv: comparison table
- results/recovered_controls/: recovered historical control JSONs
- results/self_debias/: saved Self-Debiasing results

## Important limitations
- Historical CDA controls came from earlier checkpoints and remain archived separately. Fresh matched controls were subsequently run on the final CDA checkpoints for English and Urdu, seeds 0–4.
- Self-Debiasing controls use the same seeded MF/MM/FF name-pairing procedure, English and Urdu evaluation templates, top-k setting, chi-square test, and gender-effect formula as the standard DisCo controls. However, Self-Debiasing modifies and renormalizes token probabilities before evaluation. Results should therefore be interpreted as an adapted DisCo evaluation rather than an identical scoring implementation.
- Trained CDA model weights are not included in this package.
- Lower raw DisCo scores alone do not establish reduced gender bias.
## CDA Training Configuration

The English, Urdu, and English+Urdu CDA models were fine-tuned from xlm-roberta-base using masked language modeling (MLM). The following hyperparameters are documented in the training notebooks for all five CDA variants. Training was configured for 500 optimizer steps per model rather than a fixed number of epochs. Hindi-only and Hindi+Urdu training used filtered counterfactual sentence pairs, with balanced language sampling in the combined setup. 

| Parameter | Value |
|---|---|
| Base model | XLM-RoBERTa Base |
| Learning rate | 2e-5 |
| Per-device batch size | 4 |
| Gradient accumulation steps | 2 |
| Effective batch size | 8 |
| Maximum sequence length | 128 tokens |
| Training steps | 500 per model |
| MLM masking probability | 0.15 |
| Precision | FP16 |
| Random seed | 42 |
| Hardware | NVIDIA Tesla T4 GPU |
| Training framework | PyTorch / Hugging Face Transformers |

### Training Data

- **CDA-English:** English counterfactual sentence pairs from `data/cda/en_pairs.jsonl` (9,972 pairs).
- **CDA-Urdu:** Urdu counterfactual sentence pairs from `data/cda/pairs_ur.jsonl` (9,972 source pairs, with filtering applied before training).
- **CDA-Combined:** English and filtered Urdu counterfactual examples combined for training.



### Training Dataset Sizes

| CDA variant | Training data | Training sentences |
|---|---|---:|
| English-only | 9,972 English pairs | 19,944 |
| Urdu-only | 7,840 filtered Urdu pairs | 15,680 |
| English+Urdu | 7,840 English + 7,840 Urdu pairs | 31,360 |
| Hindi-only | 6,990 filtered Hindi pairs | 13,980 |
| Hindi+Urdu | 6,990 Hindi + 6,990 Urdu pairs | 27,960 |

Hindi and Urdu datasets each contained 9,972 source pairs before filtering. Training examples include both original and counterfactual sentences.

### Training Duration

Training was configured for 500 optimizer steps per model rather than a fixed number of epochs. The effective number of epochs depends on the size of the training dataset.

### Reproducibility

CDA training notebooks are available at:

- `notebooks/stream2_cda_training_recovered.ipynb`
- `notebooks/stream2_cda_hindi_training.ipynb`

The notebooks document the training workflows and hyperparameters for all five CDA variants. Trained model checkpoints are not stored in the GitHub repository.

## Final CDA Evaluation

The final CDA checkpoints were evaluated using DisCo.
English and Urdu evaluations used their respective templates.
Urdu evaluations used `data/templates/v2`.

For the English, Urdu, and English+Urdu CDA variants,
matched controls were run using `src.disco.control`
with random seeds 0–4.

Hindi-only and Hindi+Urdu CDA checkpoints were evaluated
on Urdu using the same Urdu template directory and
five matched-control seeds.

### Final Results

| Model | Language | DisCo score | Mean gender effect | SD gender effect |
|---|---|---:|---:|---:|
| cda_en_full | en | 0.6134 | -0.0144 | 0.0209 |
| cda_en_full | ur | 0.8337 | 0.0349 | 0.0139 |
| cda_ur_full | en | 0.7337 | 0.0045 | 0.0181 |
| cda_ur_full | ur | 0.5531 | 0.0163 | 0.0132 |
| cda_en_ur_full | en | 0.6429 | 0.0051 | 0.0151 |
| cda_en_ur_full | ur | 0.6990 | 0.0433 | 0.0216 |
| cda_hi_full | ur | 0.6704 | 0.0380 | 0.0173 |
| cda_hi_ur_full | ur | 0.5827 | 0.0286 | 0.0127 |

### Interpretation

- English-only CDA had the lowest English DisCo score
  among the evaluated CDA variants.
- Urdu-only CDA had the lowest Urdu DisCo score
  among the evaluated CDA variants.
- Hindi+Urdu CDA had a lower Urdu DisCo score
  than Hindi-only CDA.
- These are descriptive findings, not statistical proof
  of a reduction in gender bias.
- Gender-effect values are signed contrasts between
  mixed-gender and same-gender name-pair controls.

### Evaluation Artifacts

- `final_cda_comparison.json`
- `final_cda_comparison.csv`
- `stream2_final_evaluation/` — 6 DisCo results and 30 controls
- `stream2_hindi_final/` — 2 DisCo results and 10 controls

### Outstanding Verification

- Interpret Self-Debiasing results separately, accounting for the adapted prediction probabilities.


## Baseline comparison (matched controls, verified)

The baseline XLM-R controls in `results/recovered_controls/control_{en,ur}_xlm-roberta-base_seed0-4.json`
use the same templates (Urdu: `data/templates/v2`), name lists, seeds and `src.disco.control` code as the
final CDA controls, so they are directly comparable. Urdu baseline gender effect: 0.052 ± 0.008 (5 seeds).

Urdu gender effect, each model vs baseline (5 seeds; seed n uses the same name split for every model,
so a paired t-test is used):

| Model (tested on Urdu) | Gender effect | Change vs baseline | p (paired) |
|---|---:|---:|---:|
| Baseline XLM-R | 0.052 | – | – |
| cda_ur_full | 0.016 | −0.036 | 0.001 |
| cda_hi_ur_full | 0.029 | −0.024 | 0.020 |
| cda_hi_full | 0.038 | −0.014 | 0.074 |
| cda_en_full | 0.035 | −0.017 | 0.130 |
| cda_en_ur_full | 0.043 | −0.009 | 0.474 |
| Self-Debiasing | 0.043 | −0.009 | 0.220 |

- Urdu-only CDA reliably reduces the Urdu gender effect (holds after Bonferroni correction for 6 tests, α = 0.0083).
- Hindi+Urdu CDA is suggestive (p = 0.02, not significant after correction); other setups show no reliable change.
- Most of the drop in raw DisCo scores after CDA comes from lower same-gender scores (less sensitivity to names in general), not from a smaller gender effect.
- Self-Debiasing raises raw Urdu DisCo (0.877 → 0.928) but also raises same-gender scores (0.885), with no reliable change in the gender effect.

Caveats: the 5 seeds vary only the name split; each CDA model was trained once (seed 42), so training
randomness is not included. Models were trained for 500 steps × effective batch 8 = 4,000 sentences,
i.e. ~13–29% of each training set.
