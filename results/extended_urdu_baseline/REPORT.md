# Extended Urdu XLM-R baseline and controls

Full baseline (70 pairs): extended 0.852679; original Urdu v2 0.876531; difference -0.023852.

Gender effect = MF - (MM + FF) / 2. Controls use 35 pairs per comparison.

| Seed | MF | MM | FF | Same-gender average | Gender effect |
|---|---:|---:|---:|---:|---:|
| 0 | 0.855357 | 0.804167 | 0.798810 | 0.801488 | +0.053869 |
| 1 | 0.846429 | 0.794643 | 0.804762 | 0.799702 | +0.046726 |
| 2 | 0.858333 | 0.813095 | 0.800000 | 0.806548 | +0.051786 |
| 3 | 0.850595 | 0.788095 | 0.800595 | 0.794345 | +0.056250 |
| 4 | 0.866071 | 0.800000 | 0.793452 | 0.796726 | +0.069345 |

Extended gender effect: 0.055595 +/- 0.008450 (sample SD, five seeds).
Original v2 gender effect: 0.052245 +/- 0.007950.

Historical v2 results use different library versions; interpret differences cautiously. Seeds vary name splits only. Raw DisCo scores include name-to-name variation.

Run: `python -m src.disco.evaluate_extended`
Predictions are cached and reused without changing the repository scoring function.

Mean gender-effect change vs v2: +0.003350. The lower raw DisCo score does not establish reduced gender bias; the matched gender effect is slightly higher. No significance claim is made.
