# Stream 2: CDA and Self-Debiasing

## Methods
- Base model: XLM-RoBERTa-base
- CDA variants: English, Urdu, and combined English+Urdu
- Evaluation: DisCo on English and Urdu templates
- Same-gender controls: MF, MM, FF across five seeds
- Self-Debiasing: experimental inference-time adaptation

## Results
- results/stream2_cda_retrained.json: latest CDA DisCo scores
- results/stream2_final_comparison.csv: comparison table
- results/recovered_controls/: recovered historical control JSONs
- results/self_debias/: saved Self-Debiasing results

## Important limitations
- Historical CDA controls were generated using earlier checkpoints.
  They must not be treated as matched controls for the retrained models.
- The Self-Debiasing controls used a different name-pairing procedure
  and are not directly comparable to the CDA control effects.
- Trained CDA model weights are not included in this package.
- Lower raw DisCo scores alone do not establish reduced gender bias.
