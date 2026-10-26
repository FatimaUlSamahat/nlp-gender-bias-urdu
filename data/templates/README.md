# Templates

Format (same as the authors' code expects): one JSON file per language, named
`disco_templates_<lang>.json`, with keys "male" and "female", each a list of sentences
using the placeholders {PERSON} and {BLANK}. The i-th male and i-th female sentence are a pair.

- `disco_templates_en.json`  the 14 English templates, copied from Webster et al. (2020), Appendix A.
- `disco_templates_ur.json`  TODO (Urdu owner). Male/female versions differ in the verb (karta/karti).
- `extended/`                TODO: our larger template sets, kept separate from the original 14.

Rule: never edit the original 14 once committed. Put anything new in a new file.
