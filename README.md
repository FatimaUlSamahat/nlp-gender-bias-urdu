# Gender bias across languages: English vs Urdu (CS 5316 NLP, Fall 2026)

Reproduces and extends Vashishtha, Ahuja, Sitaram (2023), "On Evaluating and Mitigating Gender Biases in
Multilingual Settings" (Findings of ACL), adding Urdu.

Members: Eshal Faisal, Laiba Naeem, Abeeha Imran, Fatima Ul Samahat.

## Layout
- `data/templates/`   DisCo templates (en = 14 from Webster et al. 2020; ur = ours)
- `data/names/`       gendered name lists
- `src/`              our code (copy from third_party/ then edit here)
- `third_party/`      authors' original code, unmodified, MIT licensed (we must disclose reuse)
- `results/`          small result files (JSON/CSV)
- `notebooks/`        exploration, one per person
- `report/`           report and slides
- `PLAN.md`           who does what and when; `CONTRIBUTING.md` git rules

## Setup
```
git clone <repo-url>
cd nlp-gender-bias-urdu
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
