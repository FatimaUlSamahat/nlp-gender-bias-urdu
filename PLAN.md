# Plan (2 weeks, 4 people). Names are placeholders: each person picks one stream.

Stream 1 PIPELINE + REPRODUCTION  (folder: src/disco/, results/disco_*)
Stream 2 DEBIASING (CDA + Self-Debiasing)  (folder: src/debias/, results/debias_*)
Stream 3 URDU DATA  (folder: data/, results/data_checks_*)
Stream 4 EXTENSION + ANALYSIS + REPORT  (folder: src/extension/, src/analysis/, report/)

## Hand-offs (so nobody is blocked)
- Stream 3 -> everyone: disco_templates_ur.json + ur_names.json v1 by Day 4 (rough is fine, native-speaker fixes later).
- Stream 1 -> everyone: script `python -m src.disco.run --lang <l> --model <m>` writing results JSON, by Day 3.
- Stream 2 needs Urdu counterfactual text from Stream 3 by Day 7.
- Stream 4 needs result JSONs from 1 and 2 by Day 10 for plots.

## Timeline
Days 1-2: everyone reads the paper; repo + env working; GPU notebook working; Urdu owner starts templates.
Days 3-5: English/Hindi DisCo reproduced (S1); CDA code skeleton (S2); Urdu v1 files (S3); extended English template set draft (S4).
Days 6-9: CDA/Self-Debias runs (S2); Urdu DisCo scores + Hindi->Urdu transfer (S1+S3); extension experiment (S4).
Days 10-12: analysis, plots, native-speaker review fixes, stats.
Days 13-14: report + presentation, final check, tag the release.
