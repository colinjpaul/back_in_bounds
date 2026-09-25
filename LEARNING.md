# Learning Path — Back in Bounds

Colin's job-search learning plan, worked through **on this repo**. Each step is a real change to Back in Bounds, so the learning and the portfolio grow together.

**Priority:** Playwright → Python for QA → SQL → Python for SQL
**Study time:** weekdays 08:30–10:30
**Progress checklist:** ticked off on the Learning path panel of Colin's *Week & Scorecard* dashboard. Step IDs (PW1, Q1, S1…) match that checklist. Update the `[ ]` boxes here as well if useful.

## How to help (for Claude in VS Code)

- Teach, don't just do. Explain the concept, then let Colin write the code; review it and suggest improvements.
- One step per session. Start by asking which step Colin is on, and check what already exists in the repo first.
- Keep changes small and committed per step, with a clear commit message.
- Don't break the existing suites: `pytest test_golf_app_v8.py` (Tier 1) and `pytest test_playwright_e2e.py` (Tier 2, needs the app running on :8050).

---

## 1 · Playwright (Python) — extend `test_playwright_e2e.py`

Already in place: 5 E2E tests (header, tabs, course selector, hole selector, upload widget).

- [ ] **PW0** Do this first, manually: with the app running, change one value in `data/fermoy_rounds.csv` and one in `data/Launch Monitor Data.csv`, then confirm both changes show in the app (Round Analysis for Fermoy, Range Sessions for that club). Note whether a restart was needed, then undo the edits. This becomes the spec for an automated data-to-UI test later.
- [ ] **PW1** Setup check: run the existing suite with `pytest-playwright`, then with `--headed` and `--slowmo 500` to watch it. Add a `pytest.ini` with `base_url` so tests stop hardcoding `BASE_URL`.
- [ ] **PW2** Locators: rewrite the CSS/ID locators with `get_by_role`, `get_by_text`, `get_by_test_id`. Add `data-testid` attributes to key Dash components where needed.
- [ ] **PW3** Assertions: replace any manual waits with `expect()` auto-waiting; add assertions on metric card values (Average Score, GIR %, Putts) for a known course.
- [ ] **PW4** Interactions: test the Range Sessions tab — club dropdown, scatter chart renders, single-club deep dive updates.
- [ ] **PW5** Fixtures: move app start-up into a session fixture in `conftest.py` (start `golf_app_v8.py` in a subprocess, wait for :8050) so the suite runs with one command.
- [ ] **PW6** Page Object Model: create `pages/round_analysis_page.py` and `pages/range_page.py`; refactor tests to use them.
- [ ] **PW7** API/network: use `page.route()` or `request` to check Dash callback responses (`/_dash-update-component`) return 200 and expected data.
- [ ] **PW8** Debugging: turn on tracing for failures (`--tracing retain-on-failure`), open a trace in the Trace Viewer, and add screenshots on failure.
- [ ] **PW9** Cross-browser and parallel: run on Chromium, Firefox and WebKit; add `pytest-xdist` and run with `-n auto`.
- [ ] **PW10** CI: GitHub Actions workflow that installs deps, starts the app, runs Tier 1 + Tier 2, and uploads traces as artifacts. Add the status badge to the README.

## 2 · Python for QA — `test_golf_app_v8.py`

Already in place: 19 pytest tests and the hand-rolled `run_tests_v8.py` runner.

- [ ] **Q1** pytest basics: run with `-v`, `-k`, `-x`, `--lf`; read the output of a deliberately failing test.
- [ ] **Q2** Fixtures and parametrize: move shared setup into `conftest.py`; parametrize the date-cleaning and iron-gapping tests with edge cases.
- [ ] **Q3** Markers: add `@pytest.mark.ocr`, `unit`, `callback`, `e2e`; register them in `pytest.ini`; skip OCR tests cleanly when `tesseract` is missing.
- [ ] **Q4** API testing: write `requests` + pytest tests against the running app's HTTP endpoints (status codes, response shape).
- [ ] **Q5** Test data: move test inputs into `tests/data/*.csv` / `*.json` and load them via fixtures.
- [ ] **Q6** Reporting: generate a `pytest-html` (or Allure) report; link a sample in the README.

## 3 · SQL — `data/analytics.db`

Built by `export_to_sqlite.py` (tables: `fermoy_rounds`, `range_sessions`). Practise in DB Browser for SQLite, the VS Code SQLite extension, or the `sqlite3` CLI. Save good queries in `sql/`.

- [ ] **S1** `SELECT`, `WHERE`, `ORDER BY`, `LIMIT`: best 5 rounds; all rounds over 85.
- [ ] **S2** Aggregates: average score, putts and GIR per month with `GROUP BY` / `HAVING`; average carry per club.
- [ ] **S3** JOINs: add a `courses` (or `holes`) table and join it to rounds; use a `LEFT JOIN` to find rounds with no matching course.
- [ ] **S4** Subqueries and CTEs: rounds better than your average; a CTE for front-nine vs back-nine comparison.
- [ ] **S5** Window functions: rolling 3-round average (`AVG() OVER`), `RANK()` rounds by score, running putt totals.
- [ ] **S6** Data-quality checks: SQL that finds duplicate rounds, NULL hole scores, totals that don't equal the sum of holes. Wire these into pytest as data tests.
- [ ] **S7** Writes: `INSERT` a round, `UPDATE` a mistake, wrap it in a transaction and roll back.

## 4 · Python for SQL — connect the app to the database

- [ ] **PS1** `sqlite3` in Python: connect, run parameterised queries (never string-format SQL).
- [ ] **PS2** pandas `read_sql` and `to_sql`: refactor `export_to_sqlite.py` to use them cleanly and idempotently.
- [ ] **PS3** pandas essentials: load rounds from SQLite instead of CSV in the app; select, filter and clean with pandas.
- [ ] **PS4** pandas `groupby` / `merge` next to the equivalent SQL from S2/S3; confirm both give the same numbers in a test.
- [ ] **PS5** SQLAlchemy: create an engine so the app could switch from SQLite to PostgreSQL by changing one URL.
- [ ] **PS6** Test the data layer: pytest fixtures that build a temporary SQLite DB, load sample rows, and test your queries.

## Portfolio milestones

- [ ] **F1** Playwright suite running green in GitHub Actions (PW10).
- [ ] **F2** App reading from SQLite, with SQL analysis queries in `sql/` and data-quality tests (S6, PS3).
- [ ] **F3** README updated with the CI badge, test report and a short "what I learned" section.

## Later: pandas and data science

Reshaping (`pivot_table`, `melt`), time series (`resample`, `rolling`), seaborn charts, NumPy, and a first scikit-learn model (e.g. predict score from putts and GIR).
