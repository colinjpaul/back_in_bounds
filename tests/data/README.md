# Test data (made up — not real rounds)

These files are **mock data for tests only**. The app's real data stays in `data/fermoy_rounds.csv`.
Columns match the live set used by the app (`Total_Score`, `Front9`, `Back9`, `H1_Score`…`H18_Putts`) — the old duplicate columns from [DEF-004](../../docs/defects/DEF-004-duplicate-score-columns.md) are deliberately left out.

## `fermoy_rounds_sample.csv` — 10 clean rounds

Every row is internally consistent: `Front9` = sum of H1–H9 scores, `Back9` = sum of H10–H18, `Total_Score` = `Front9` + `Back9`. Rounds are weekly Sundays from 2026-06-07 to 2026-08-09, titled `Sample Round 01`–`10`.

### Expected answers

| Check | Expected |
|---|---|
| Number of rounds | 10 |
| Average `Total_Score` | **85.5** |
| Best round | 79 on 2026-06-21 (Sample Round 03) |
| Worst round | 92 on 2026-06-28 (Sample Round 04) |
| Average `Front9` / `Back9` | 42.5 / 43.0 |
| Average putts per round | 36.6 |
| Total greens in regulation (all rounds) | 78 |

Totals in date order: 84, 88, 79, 92, 86, 83, 90, 81, 87, 85.
Putts per round: 32, 42, 38, 33, 42, 34, 37, 35, 33, 40.
GIR per round: 7, 8, 11, 3, 9, 9, 6, 8, 7, 10.

## `fermoy_rounds_edge_cases.csv` — 3 deliberately bad rows

For negative tests and data-quality checks (LEARNING.md steps Q5 and S6). Each row's `Round_Title` says what's wrong:

| Date | Problem | A good check should… |
|---|---|---|
| 2026-09-01 | `H7_Putts` is blank | flag the missing value |
| 2026-09-02 | `Total_Score` is 5 higher than the hole scores add up to | flag the mismatch |
| 2026-09-01 (again) | duplicate date | flag the duplicate |
