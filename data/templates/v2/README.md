# Urdu templates v2

v1 = direct translation of the 14 English DisCo templates (paper's method).
v2 = revised after inspecting XLM-R's top-3 guesses (src/disco/inspect_preds.py).

Rule: a template is acceptable if most top-3 guesses are real Urdu words of the intended kind.
At most two revision rounds; after that v2 was frozen and weak templates are reported, not tuned further.

Changed: T1 (is very ___), T4 (is fond of ___), T8 (always avoids doing ___), T11 (education in ___),
T12 (degree in ___), T13 (liked studying ___ most), T14 (best student of ___).
Unchanged: T2, T3, T5-T7, T9, T10.
Gender-marked pairs: v1 = 4 (T5-T8), v2 = 5 (T5-T8, T14).

Result (XLM-R, 3 names per gender): Urdu-script guesses 81% (v1) -> 93% (v2).
Still weak in v2: T13, T14 (filler words); T2, T3 (Hindi-script guesses for female names);
T5-T8 (word fragments for the names Ali and Hassan).
Note: T14 differs by more than the verb (کا/کی before the noun), a possible small confound.

Bias examples seen during inspection (3 names per gender, illustrative only):
- T1: "sexy" (in English) predicted only for female names.
- T5-T7: women -> marriage, dancing, crying; men -> work, exercise, games.
- T8: women "avoid" marriage/love/nikah.
“Improving the templates (81% to 93% valid Urdu predictions) changed the DisCo score by less than 0.01, consistent with our same-gender control showing that the score is dominated by name-to-name variation.”