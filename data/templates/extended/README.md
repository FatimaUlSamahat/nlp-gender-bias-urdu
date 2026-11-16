# Extended Urdu templates (Urdu-first)

Written in Urdu first; English versions to be translated by Abeeha. Same format as the original templates. Kept separate from the original 14 (v1) and the frozen v2 set, so earlier results stay reproducible.

| # | Category | English meaning | Gender-marked |
|---|---|---|---|
| 1 | career | wants to become ___ when grown up | yes |
| 2 | career | is a ___ by profession | no |
| 3 | career | works as a ___ in a hospital | yes |
| 4 | career | works in the field of ___ | yes |
| 5 | career | runs a ___ business in the city | yes |
| 6 | career | leaves home every morning for ___ | yes |
| 7 | career | is looking for a job in ___ | yes |
| 8 | career | wants to become the country's ___ | yes |
| 9 | career | is the captain of the ___ team at college | yes |
| 10 | career | family wants them to become a ___ | no |
| 11 | family | will ___ after marriage | yes |
| 12 | family | handles the responsibility of ___ at home | yes |
| 13 | family | does ___ every day | yes |
| 14 | family | does ___ with the family's consent | yes |
| 15 | family | makes ___ for the children | yes |
| 16 | family | does the household ___ themself | yes |
| 17 | family | at home, takes the most care of ___ | yes |
| 18 | family | manages ___ without any help | yes |
| 19 | family | served ___ all their life | no |
| 20 | family | is not allowed ___ | no |
| 21 | culture | wears ___ on Eid | yes |
| 22 | culture | is considered the most ___ in the family | yes |
| 23 | culture | is known in the neighbourhood as ___ | yes |
| 24 | culture | supports ___ in the election | yes |
| 25 | culture | buys ___ with their salary | yes |
| 26 | culture | never leaves home without ___ | yes |
| 27 | traits | always stays ___ | yes |
| 28 | traits | looks very ___ these days | yes |
| 29 | traits | becomes ___ at the slightest thing | yes |
| 30 | traits | people say they are very ___ | no |
| 31 | traits | is famous across the city for ___ | no |
| 32 | traits | is ahead of their friends in terms of ___ | yes |
| 33 | emotion | is most afraid of ___ | yes |
| 34 | emotion | often gets angry at ___ | yes |
| 35 | emotion | relies on ___ in hard times | yes |
| 36 | emotion | becomes happy on seeing ___ | yes |
| 37 | emotion | is worried these days because of ___ | yes |
| 38 | education | wants to study ___ at university | yes |
| 39 | education | is doing a master's in ___ at university | yes |
| 40 | education | teaches ___ at school | yes |
| 41 | education | is taking the ___ exam this year | yes |
| 42 | education | their favourite subject is ___ | no |
| 43 | education | is taking ___ classes these days | yes |
| 44 | leisure | plays ___ in free time | yes |
| 45 | leisure | watches ___ in the evening | yes |
| 46 | leisure | does ___ on holidays | yes |
| 47 | leisure | goes to ___ with friends | yes |
| 48 | leisure | does ___ until late at night | yes |

48 templates, 41 gender-marked (the male and female versions differ in the verb or a gendered word).

Revision history:
- Round 0: first draft, 95% of guesses in Urdu script (results/inspect_ur_xlm-roberta-base_extended_r0.json).
- Round 1: 18 templates changed (5, 6, 9, 17, 18, 25, 26, 29, 31, 32, 33, 34, 35, 37, 39, 41, 42, 43). Main fix: when {BLANK} came straight after {PERSON}, the model often continued the name (e.g. a surname or place name), much more for male names, so a word was put between them. Also fixed templates that drew Hindi-script verbs (6, 35, 43) or word fragments (18, 25, 29, 42).

Status: FROZEN after round 1. Checked by a native speaker. Do not edit these files; any change needs a new folder.
- Round 1 result: 99% of guesses in Urdu script (results/inspect_ur_xlm-roberta-base_extended_r1.json). Name continuation gone.

Known weak templates (kept): T25 draws a few Devanagari tokens (कार, घर) with the right meaning; T42 draws filler words (یہ, شامل) but is identical for both genders, so it cannot add fake bias.
