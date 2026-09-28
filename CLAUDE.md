# Back in Bounds

Plotly Dash golf analytics app and QA showcase. See README.md for architecture and test tiers.

## Learning plan

Colin is using this repo to learn Playwright, Python for QA, SQL and Python for SQL, in that order. Read **LEARNING.md** at the start of a session and follow its "How to help" section.

## Handoff notes (from Colin's planning chat in the Claude desktop app)

Colin also plans with Claude in the desktop app. That chat can't talk to this one, so notes land here.

- **2026-09-28**
  - Back in Bounds is now treated as a **test lab**: no new golf features, no more real rounds. See the top of LEARNING.md.
  - PW0 manual check found **DEF-004**: duplicate score columns in `data/fermoy_rounds.csv` (`TotalScore` vs `Total_Score`, etc.). The app reads only `Total_Score`/`Front9`/`Back9`. Write-up: `docs/defects/DEF-004-duplicate-score-columns.md`. Status: open, not yet fixed.
  - Added mock test data in `tests/data/` (10 clean sample rounds + 3 edge-case rows, expected answers in `tests/data/README.md`). Not wired into any tests yet; that's step Q5.
  - If the 23 Aug row in `data/fermoy_rounds.csv` still shows `TotalScore` = 87 or `Total_Score` ≠ 82, that was a manual test edit: put it back to 82.
