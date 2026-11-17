# Archived result files (not final)

- disco_*_cda_en_ur.json / *_cda_en_ur_v2.json: earlier evaluation runs of cda_en_ur_full (13 Nov);
  scores are identical to the final *_stream2_final.json files.
- control_*_full.json (no seed in name): copies of the seed-4 control run, left over because
  src/disco/control.py writes one file per model and each seed overwrote it.
  The final controls are results/control_*_seed0-4.json.
