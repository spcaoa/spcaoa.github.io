# Sobha Palm Court — residents' finance pages

Public, plain-language pages for owners and residents of Sobha Palm Court (Bengaluru): where the association's money goes, the shortfall and the plan, the reserves, the residents' survey, and lift/complaint performance.

- Built pages: `docs/` (served by GitHub Pages).
- Generator: `python3 tools/build.py` — reads the Managing Committee's data (`../spc-finance-site/site/data/*.csv`) plus `data/*.json|csv` here, writes `docs/`.
- Passcode curtain: `tools/passcode.txt` (git-ignored). Empty file = no gate. Only the SHA-256 hash is published; it is a curtain for casual visitors, not security. Everything in this repository is public.
- Monthly update: import the accountant's statement in the MC site, edit `data/lifts.csv` and `data/complaints.csv`, update `UPDATED` in `tools/build.py`, build, commit, push.
