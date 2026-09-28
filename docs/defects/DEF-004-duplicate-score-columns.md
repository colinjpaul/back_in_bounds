# DEF-004: Duplicate score columns in `fermoy_rounds.csv` — edits to one set are silently ignored

| | |
|---|---|
| **Status** | Open |
| **Severity** | Low: no data loss today, but the CSV has two sources of truth for the same values, and editing the "wrong" one changes nothing in the app with no warning |
| **Component** | `data/fermoy_rounds.csv`, `parse_and_append_round_ocr()` and `update_course_selection()` in `golf_app_v8.py`, `test_golf_app_v8.py` |
| **Found** | 2026-09-28, during a manual data-to-UI check (LEARNING.md step PW0): changed a round's total in the CSV and the app didn't reflect it |
| **Reproducible at** | commit `497c9f4` |
| **Environment** | macOS, Python 3.12, Chromium |

## Summary

`data/fermoy_rounds.csv` carries two parallel sets of round-level score columns:

| Old set | New set |
|---|---|
| `TotalScore` | `Total_Score` |
| `FrontScore` | `Front9` |
| `BackScore` | `Back9` |

The app only reads the new set. The old set is dead data that nothing in the app uses, but it sits next to the live columns looking just as valid. Editing the old columns changes nothing on screen, and nothing flags that the two sets now disagree.

## Steps to reproduce

1. Start the app: `python golf_app_v8.py` and open http://127.0.0.1:8050.
2. On Round Analysis, select **Fermoy Golf Club** and note the **Avg Score** card (84.0 with the two logged rounds, 86 and 82).
3. In `data/fermoy_rounds.csv`, change **`TotalScore`** (column 3) on the 2026-08-23 row from 82 to 87. Save.
4. Refresh the app / reselect Fermoy.

## Expected

Either the Avg Score updates to 86.5, or there is only one total-score column, so there is no way to edit the wrong one.

## Actual

Avg Score stays at 84.0. The app reads `Total_Score` (column 6), which is still 82. The row now says 87 in one column and 82 in another, and its hole scores sum to 82.

## Root cause

- The CSV originally used `TotalScore` / `FrontScore` / `BackScore`.
- The screenshot-upload feature, `parse_and_append_round_ocr()` (`golf_app_v8.py` ~line 1178), was later written to save rounds as `Total_Score` / `Front9` / `Back9`. When it appends with `pd.concat`, pandas keeps both sets of columns side by side.
- `update_course_selection()` (~line 979) reads only `Total_Score`:
  ```python
  avg_score_str = f"{rounds_df['Total_Score'].mean():.1f} Avg"
  ```
- `test_golf_app_v8.py` (~line 429) hedges between the two names instead of catching the duplication:
  ```python
  score_col = 'Total_Score' if 'Total_Score' in rounds_df.columns else 'TotalScore'
  ```
  This masks the problem rather than failing on it.

## Proposed fix

1. Standardise on `Total_Score` / `Front9` / `Back9` (the names the app and upload already use).
2. Remove `TotalScore`, `FrontScore`, `BackScore` from `data/fermoy_rounds.csv`.
3. Remove the name-hedging in `test_golf_app_v8.py` so tests use one column name.
4. Add a data-quality test that fails if:
   - any of the old column names reappear, or
   - `Total_Score != Front9 + Back9`, or
   - `Front9` / `Back9` don't equal the sum of `H1–H9` / `H10–H18` scores.

## Notes

- Found by a manual check, not by automation: none of the existing Tier 1–3 suites look at the CSV's column set or cross-check totals against hole scores. The data-quality test in the fix (LEARNING.md step S6) closes that gap.
- If you reproduce this, put `TotalScore` back to 82 afterwards. The real-data test in `test_golf_app_v8.py` expects the 23 Aug round to total 82.
