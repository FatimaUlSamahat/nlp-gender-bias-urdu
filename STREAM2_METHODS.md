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
## CDA Training Configuration

All CDA models were fine-tuned from `xlm-roberta-base` using masked language modeling (MLM).

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

The exact number of training examples after filtering should be verified from the training notebook or logs.

### Training Duration

Training was configured for 500 optimizer steps per model rather than a fixed number of epochs. The effective number of epochs depends on the size of the training dataset.

### Reproducibility

The CDA training notebook is available at `notebooks/stream2_cda_training_recovered.ipynb`.

The notebook documents the training workflow and hyperparameters. Trained model checkpoints are not stored in the GitHub repository.
