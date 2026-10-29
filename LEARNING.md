# Learning Path — Back in Bounds (QA track)

Colin's QA learning plan, worked through **on this repo**. Each step is a real change to Back in Bounds, so the learning and the portfolio grow together.

**Back in Bounds is a test lab.** No new golf features and no need for more real rounds. The work here is testing the app: automated tests, test data and CI. Where tests need data, use small, controlled test datasets (fixtures) with known expected values rather than entering real rounds.

**This repo covers:** Playwright → Python for QA
**SQL, pandas and Python for SQL** have moved to the [waiting-list](https://github.com/colinjpaul/waiting-list) repo (HSE/NTPF hospital waiting list data). See its LEARNING.md for steps S1–S7 and PS1–PS6.

**Study time:** weekday mornings, at Colin's own pace (no deadlines).
**Priority (from 2026-10-29):** getting a job comes first, so QA gets every weekday morning. The waiting-list data track is on hold after PS0 until F1 (Playwright suite green in GitHub Actions) is done.
**Progress checklist:** ticked off on the Learning path panel of Colin's *Daily Board*. Step IDs (PW1, Q1…) match that checklist. Update the `[ ]` boxes here as well if useful.

## How to help (for Claude in VS Code)

- Teach, don't just do. Explain the concept, then let Colin write the code; review it and suggest improvements.
- One step per session. Start by asking which step Colin is on, and check what already exists in the repo first.
- Keep changes small and committed per step, with a clear commit message.
- Don't break the existing suites: `pytest test_golf_app_v8.py` (Tier 1) and `pytest test_playwright_e2e.py` (Tier 2, needs the app running on :8050).

---

## 1 · Playwright (Python) — extend `test_playwright_e2e.py`

Already in place: 5 E2E tests (header, tabs, course selector, hole selector, upload widget).

- [x] **PW0** Do this first, manually: with the app running, change one value in `data/fermoy_rounds.csv` and one in `data/Launch Monitor Data.csv`, then confirm both changes show in the app (Round Analysis for Fermoy, Range Sessions for that club). Note whether a restart was needed, then undo the edits. This becomes the spec for an automated data-to-UI test later.
  - *Done 2026-09-28.* Found [DEF-004](docs/defects/DEF-004-duplicate-score-columns.md) (duplicate score columns). Follow-up on 2 Oct: Fermoy edits show after a browser refresh, but Launch Monitor edits need an app restart ([DEF-005](docs/defects/DEF-005-stale-launch-monitor-data.md)).
- [x] **PW1** Setup check: run the existing suite with `pytest-playwright`, then with `--headed` and `--slowmo 500` to watch it. Add a `pytest.ini` with `base_url` so tests stop hardcoding `BASE_URL`.
  - *Done 2026-10-02.* `pytest.ini` sets `base_url = http://127.0.0.1:8050` and the tests now call `page.goto("/")`.
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
  - *In progress.* `tests/data/fermoy_rounds_sample.csv` and `fermoy_rounds_edge_cases.csv` exist with expected answers in `tests/data/README.md`. Next: a `conftest.py` fixture that loads them, and tests that use it.
- [ ] **Q6** Reporting: generate a `pytest-html` (or Allure) report; link a sample in the README.

## Portfolio milestones

- [ ] **F1** Playwright suite running green in GitHub Actions (PW10).
- [ ] **F3** README updated with the CI badge, test report and a short "what I learned" section.

(F2, the SQL and data-quality milestone, now lives in the waiting-list repo.)
