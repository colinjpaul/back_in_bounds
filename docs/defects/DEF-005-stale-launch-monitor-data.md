# DEF-005: Practice tab shows stale data after `Launch Monitor Data.csv` is edited, until the app restarts

| | |
|---|---|
| **Status** | Open |
| **Severity** | Low: no data loss, but the Practice tab (and `analytics.db`) quietly disagree with the CSV, and nothing says the data is out of date |
| **Component** | Module-level data load in `golf_app_v8.py` (lines 63–85), `update_dashboard()` (~line 885), `sync_csv_to_sqlite()` call at startup (~line 508) |
| **Found** | 2026-10-02, during a manual data-to-UI check: edited a club speed in the CSV while the app was running and the Practice tab didn't change |
| **Reproducible at** | commit `08042f6` |
| **Environment** | macOS, Python 3.12, Chromium, app started with `app.run(debug=True)` |

## Summary

The app reads `data/Launch Monitor Data.csv` once, when the script starts, into a global DataFrame `df`. Every Practice-tab chart is built from that in-memory copy. Edits made to the CSV while the app is running never reach the UI, even after a browser refresh. The same goes for the `range_sessions` table in `data/analytics.db`, which is synced only at startup.

The Fermoy rounds data doesn't work this way. `load_fermoy_rounds()` re-reads `fermoy_rounds.csv` on every callback, so edits to that file do show up after a refresh. The app handles its two CSVs in two different ways.

## Steps to reproduce

1. Start the app: `python golf_app_v8.py` and open http://127.0.0.1:8050.
2. Go to the **Practice** tab and select **LW (58)** in the club selector. Hover the 21-05-26 point: Club Speed **74.2**.
3. With the app still running, in `data/Launch Monitor Data.csv` change **Club Speed** on the `21-05-26, LW (58)` row from 74.2 to 81.8. Save.
4. Refresh the browser and reselect LW (58).
5. Optional: `sqlite3 data/analytics.db "select Date, Club, \"Club Speed\" from range_sessions where Club like 'LW%';"`

## Expected

The Practice tab charts (the bag-gapping scatter and the per-club charts) show Club Speed 81.8 for that shot after a refresh. This is how the Round Analysis tab already behaves with `fermoy_rounds.csv`.

## Actual

- The charts still show 74.2.
- `range_sessions` in `analytics.db` still has 74.2.
- Both update only after the app is stopped and restarted.

Observed 2026-10-02: the app process started at 10:12 and the CSV was saved at 10:22. The CSV said 81.8, while the UI and DB said 74.2.

## Root cause

- The CSV is loaded once, at import time (`golf_app_v8.py` lines 63–69):
  ```python
  csv_path = ensure_launch_monitor_csv()
  df = pd.read_csv(csv_path)
  ```
- `global_fig` (the bag-gapping scatter, line 72) is also built once from that `df` and passed into the layout as a fixed figure.
- `update_dashboard()` filters the global `df` instead of re-reading the file:
  ```python
  filtered_df = df[df['Club'] == selected_club].copy()
  ```
- The club-selector options (line 629) come from the same startup `df`, so a new club added to the CSV wouldn't appear either.
- `sync_csv_to_sqlite()` runs once at startup (~line 508).
- `debug=True` turns on Dash's hot reloader, but it watches `.py` files only, not data files, so it doesn't help here.

## Proposed fix

1. Add a `load_launch_monitor_data()` function that reads and cleans the CSV, mirroring `load_fermoy_rounds()`.
2. Call it inside `update_dashboard()`. Build the bag-gapping scatter in a callback (or in `render_content()` when the Practice tab is selected) instead of using the global `global_fig`.
3. Build the club-selector options from a fresh load as well.
4. Add a test: write a temporary CSV, load the Practice tab, change a value in the CSV, re-trigger the callback, and assert that the new value comes through.

## Notes

- Found by a manual check, not by automation. The existing tests start the app with a fixed CSV and never change data while it's running, so they can't see this.
- A restart works around it today.
- Separate data-quality point seen while reproducing: `Smash` is stored in the CSV, not calculated. After the edit, the row has Ball Speed 73.3 and Club Speed 81.8 (a ratio of 0.90), but still says Smash 1.04. It already didn't match before the edit (73.3 / 74.2 = 0.99). This is a candidate for a data-quality check, not part of this defect.
- If you reproduce this, put the LW (58) 21-05-26 Club Speed back to 74.2 afterwards (`git restore "data/Launch Monitor Data.csv"`).
