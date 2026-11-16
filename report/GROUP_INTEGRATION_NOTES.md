# Group integration and finalization notes

## Sources located

| Contribution | Repository evidence | Used in extension deliverables |
|---|---|---|
| English reproduction (Eshal) | Commit cef8c0c; results/disco_en_xlm-roberta-base.json | Baseline and paper-comparison context |
| Urdu template/name work and verification (Fatima; README records group review) | data/templates/v2; data/templates/extended; data/names/names_source.md; inspection results; commits fc3108b and 3b1f50a | Template methodology, provenance, qualitative evidence |
| CDA and Self-Debiasing (Laiba) | src/disco/self_debias.py; notebooks/stream2_*; results/self_debias; STREAM2_METHODS.md; final comparison CSV | Existing adaptation, historical regression checks, CDA context |
| New extension | src/extension; results/self_debias_extension; report/figures | Matched two-template experiment, context analysis, figures and report section |

These are evidence-based source associations, not a final allocation of authorship. Ask the group to confirm individual credit and the final author order.

## Master documents not located

Before preparing these deliverables, no shared final report manuscript (Word/LaTeX/PDF) or existing PowerPoint deck was found in this clone. The report folder previously contained only the generated analysis and plots. Trained CDA checkpoints are not included; the Self-Debiasing adaptation needs only the base model. No additional Abeeha-specific committed report artifact was identified. Work outside this repository was not inspected.

Ask groupmates for:

1. The latest master report and master slide deck, including any formatting/rubric or page/time limits.
2. Their final contribution paragraphs and confirmed authorship/credit assignments.
3. The authoritative final CDA checkpoint/result bundle or confirmation of the final comparison CSV, especially the combined English+Urdu model.
4. Any held-out evaluation, semantic annotations, or downstream fairness results absent from this clone.

The supplied extension deck is an insertable section, not a claim that the full group presentation has been merged or finalized.

## Resolve before submission

- Use the matched raw Urdu v2 Self-Debiasing score **0.918367**, supported by the saved JSON and rerun. README/STREAM2 text reporting approximately **0.928** conflicts with this evidence.
- Use **results/stream2_final_comparison.csv** for final CDA context. The older results/stream2_cda_retrained.json gives conflicting combined-model scores (English ~0.6141; Urdu ~0.6133), while the final CSV gives ~0.6429 and ~0.6990. Do not mix checkpoints or silently average them.
- Cite the new batched extended baseline G = **0.055714** when comparing against the new batched intervention; the earlier single-sentence result was **0.055595**. One near-tied top-three token explains the small difference.
- Full raw scores use 70 pairs; control G uses matched MF/MM/FF comparisons of 35 pairs. Do not subtract same-gender controls from the full raw score.
- Label plot errors as sample SD over name splits, not confidence intervals. The group's older paired-test claims should be qualified as exploratory; five overlapping splits and one training seed do not establish population-level reliability.
- The model revision is unresolved in the manifest (null). Preserve/identify the downloaded Hugging Face snapshot for exact long-term reproduction.
- CDA extended-template evaluations are not available. The slides distinguish historical CDA/v2 findings from new extended-template results.
- English translations of the extended set are available, but extended-English evaluation was not run.

## Suggested integration order

Place EXTENSION_REPORT_SECTION.md after the group's baseline/CDA methods and results, before the general discussion. Reuse figures 01, 02, 04 and 05 in the extension section; figure 03 supports the group-wide comparison and figure 06 belongs in the language-comparison appendix. The extension slides follow this same progression and contain speaker notes with data sources.

Existing member-owned source files have not been edited to resolve these conflicts; the required corrections are recorded here for the final editor.

## Prepared handoff

- Report section: report/EXTENSION_REPORT_SECTION.md
- Editable 11-slide deck: report/slides/URDU_EXTENSION_SLIDES.pptx
- Source/speaker notes: report/slides/SPEAKER_NOTES.md
- Six PNG/SVG figure pairs: report/figures/
- Full figure interpretation: report/RESULTS_ANALYSIS.md

Slide chart data are rounded to six decimals for portable embedded Excel workbooks. Full-precision experiment outputs remain unchanged. The deck was rendered and structurally validated; it was not opened in native PowerPoint.
