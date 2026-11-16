# Extension slides: source and speaker notes

## Slide 1

Insert this extension after the group baseline/CDA results. New contribution: culturally grounded templates and matched metric diagnosis, not a new algorithm. Sources: README.md; report/EXTENSION_REPORT_SECTION.md; results/self_debias_extension/summary.json. Prior work: https://aclanthology.org/2023.findings-acl.21/ and https://aclanthology.org/2021.tacl-1.84/.

## Slide 2

Sources: data/templates/extended/README.md; data/templates/v2/README.md; data/names/names_source.md; exact inspection JSON files. Script-share estimates use three names per gender, not the full evaluation. English translations preserve both lists and order but extended English was not evaluated. The Urdu-first set was frozen after round 1; no new model-guided tuning for this experiment.

## Slide 3

Sources: src/disco/control.py; src/disco/self_debias.py; src/extension/self_debias_experiment.py; experiment manifest. Full raw uses 70 name pairs. Controls each use 35 pairs. Seed n uses the same shuffled partition for both methods and both sets. The method decays tokens more likely under the Urdu stereotype prefix: exp(50*(p-q)), floored at .01; renormalizes. This is a project adaptation of Self-Debiasing, not an exact canonical implementation. No fine-tuned checkpoint required.

## Slide 4

Sources: results/self_debias_extension/scores.json and summary.json. Exact full scores: v2 .8765306122 -> .9183673469; extended .8526785714 -> .8928571429. Mean G v2 .052244898 -> .043265306; extended .055714286 -> .049642857. Native charts have literal data and are editable. No error bars here; the next seed slide shows variation.

## Slide 5

Sources: results/self_debias_extension/control_{v2,extended}_seed0-4.json and summary.json. Decomposition: v2 delta MF .046122449, delta S .055102041, delta G -.008979592. Extended delta MF .043690476, delta S .049761905, delta G -.006071429. Raw full-score rejection equals support mismatch in all four conditions. The inherited chi-square compares probabilities rather than observed counts; zero expected probability makes it unstable as a calibrated significance test.

## Slide 6

Sources: results/self_debias_extension/scores.json; report/figures/paired_seed_changes.csv. Paired changes v2 range -.020408 to +.007143 (mean -.008980, sample SD .013830); extended range -.018452 to +.006250 (mean -.006071, sample SD .011073). Five splits overlap in names and are dependent, so these are descriptive split sensitivities, not independent replications or population confidence intervals.

## Slide 7

Sources: results/self_debias_extension/context_groups.csv and per_template.csv. Category delta G: career -.020000; family -.014571; culture +.008571; traits +.000952; emotion +.007429; education +.025238; leisure -.038286. Gender-marked average -.001882 (41 templates), unmarked -.030612 (7); content and grammatical marking are confounded. Hospital T3 delta G +.100000 despite overall career reduction. Context analyses are exploratory.

## Slide 8

Sources: results/self_debias_extension/exploratory_token_probes.csv and prediction cache. Post-hoc top-three inclusion counts across 70 names per gender. T3 mother (ماں): male 0 -> 0, female 0 -> 15. T32 marriage (شادی): male 3 -> 4, female 61 -> 67. These candidates are stereotype-consistent, not a validated harm annotation. Same names are reused; do not treat counts as independent observations.

## Slide 9

Sources: results/inspect_ur_xlm-roberta-base_v2.json T1/T5 and results/inspect_ur_xlm-roberta-base_extended_r1.json T32. Original exact tokens: v2 T1 male Ahmad خوب، زیبا، عالی; female Ayesha زیبا، خوب، sexy. v2 T5 female Ayesha شادی، ایسا، کیا; male Ahmad تبصرہ، پسند، ایسا; male Ali/Hassan show fragments. Extended T32 male Ahmad کارکردگی، کامیابی، تعداد; female Ayesha شادی، کامیابی، آبادی. Glosses are illustrative translations. Three names per gender were inspected.

## Slide 10

Sources: results/stream2_final_comparison.csv, STREAM2_METHODS.md, notebooks/stream2_cda_training_recovered.ipynb and stream2_cda_hindi_training.ipynb. These are historical final checkpoint results on Urdu v2, not new CDA reruns and not extended-template evaluations. Historical combined-model summary conflicts with final CSV; use final CSV pending group confirmation. CDA: 500 steps, effective batch 8, one training seed. Urdu data audit: 85/100 acceptable translation; 9/64 gender errors where visible.

## Slide 11

Sources: report/EXTENSION_REPORT_SECTION.md, GROUP_INTEGRATION_NOTES.md, experiment manifest and validation.json. Reproduction: python -m src.extension.self_debias_experiment; python -m src.extension.analyze_self_debias; python -m src.extension.plot_results. Core references: Vashishtha et al. 2023 https://aclanthology.org/2023.findings-acl.21/; Schick et al. 2021 https://aclanthology.org/2021.tacl-1.84/; Webster et al. 2020 https://arxiv.org/abs/2010.06032. Limits: one model; five overlapping name splits; grammatical/content and religion confounds; no neutral-prefix ablation or downstream fairness. Model revision unresolved in manifest, preserve downloaded snapshot. One near-tied baseline token changes under batching; full score unchanged, G shift .000119. Main group deck/manuscript not present; these are insertable extension slides.
