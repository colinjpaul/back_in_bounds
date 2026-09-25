
# Back in Bounds: Golf Performance Analytics & Quality Engineering Showcase

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Dash](https://img.shields.io/badge/Dash-Plotly-11F0D5?style=for-the-badge&logo=plotly&logoColor=black)](https://dash.plotly.com/)
[![Pytest](https://img.shields.io/badge/Pytest-Unit%20%26%20Callback%20Suite-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![Playwright](https://img.shields.io/badge/Playwright-E2E%20Automation-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)](https://playwright.dev/python/)
[![SQLite](https://img.shields.io/badge/SQLite-Relational%20DB-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Claude API](https://img.shields.io/badge/Claude%20API-QA%20Agent-D97757?style=for-the-badge)](https://docs.claude.com/)

A Plotly Dash golf analytics app, built as a personal project to practice Python/data tooling and, primarily, as a **quality engineering showcase**: the same app is exercised by three layers of automated testing - a fast Pytest unit/callback suite, a Playwright browser E2E suite, and a small autonomous AI QA agent that drives the app through the Claude API and writes its own Markdown defect reports.

## 📌 Architecture & Key Features

### 1. Interactive Analytics Cockpit (`golf_app_v8.py`)
* **Round Analysis (On-Course Telemetry)**: Analytics across 16 Irish golf courses (Fermoy, Castlemartyr, Fota Island, Cork, Killarney, etc.). Displays metric cards (Average Score, Strokes Gained vs a 5 HCP target, GIR %, Putts), hole-by-hole Caddie Strategy Tips, an 18-hole Strokes Gained bar chart, and a scoring distribution donut chart.
* **Range Sessions (Practice Analytics)**: Bag gapping scatter plots, single-club deep dives, an OLS trend line (`statsmodels`), and Smash Factor tracking over time.

### 2. Computer Vision Ingestion (`pytesseract` + Pillow) — upload UI labeled "Coming Soon"
* Drag-and-drop scorecard screenshot upload, with grayscale pre-processing + `pytesseract` OCR and regex-based extraction of date/scores/putts, appended to `data/fermoy_rounds.csv`. Requires the native `tesseract` binary installed separately (e.g. `brew install tesseract`) - `pip install pytesseract` alone is not enough.
* **Real screenshots currently fail to parse.** The synthetic scorecard used in tests reads cleanly, but real captures (`data/round_captures/fermoy-*.png`) have most of their score digits inside colored circle/box annotations that Tesseract's default OCR pass drops unpredictably - confirmed via per-cell crop testing, where isolating a single digit reads correctly even when the same digit is missed reading the full page. DEF-001's rejection behavior means this fails safely (an honest error, nothing fabricated) rather than corrupting data, but it means no real screenshot currently logs a round. The UI is labeled accordingly until a per-cell OCR pass is built. In the meantime, rounds are added directly to the CSV by hand.

### 3. Relational Database Layer (`export_to_sqlite.py`)
* Syncs `data/fermoy_rounds.csv` and the launch-monitor practice CSV into SQLite tables (`fermoy_rounds`, `range_sessions`) in `data/analytics.db`, so data can be queried directly instead of only through the UI.

### 4. Exploratory Notebook (`golf_analysis.ipynb`)
* A small scratch notebook used to prototype the date-cleaning logic (`clean_and_convert_dates`) before it moved into the app. Not a full EDA - a working notes file, kept as-is.

---

## 🧪 Three-Tier Quality Assurance Framework

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       3-TIER QUALITY FRAMEWORK                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  Tier 1: Pytest Suite (~1.5s, no browser)                                   │
│  ├── Unit tests: date cleaning, iron-gapping math                          │
│  └── In-process Dash callback tests (render_content, update_dashboard, ...) │
├─────────────────────────────────────────────────────────────────────────────┤
│  Tier 2: Playwright E2E (real Chromium browser)                             │
│  └── Header/title, tab navigation, dropdown cascades, upload dropzone       │
├─────────────────────────────────────────────────────────────────────────────┤
│  Tier 3: Autonomous AI QA Agent (`qa_agent.py`)                             │
│  ├── Manual tool-use loop against the Claude API (no agent framework)       │
│  ├── Self-healing locators: reads the live DOM via a `snapshot` tool        │
│  │   instead of a hardcoded selector map                                    │
│  └── Writes a Markdown defect report + screenshots per run                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Tier 1: Pytest Unit & Callback Suite (`run_tests_v8.py` / `test_golf_app_v8.py`)
* 19 test cases covering data-cleaning functions (`clean_and_convert_dates`), the iron-gapping algorithm (`analyze_iron_gapping`), course-scorecard generation, and the Dash callbacks (`render_content`, `update_dashboard`, `update_course_selection`, `update_hole_analysis`, `display_upload_success`) called directly, without a browser.
* `run_tests_v8.py` is a small hand-rolled runner (no `pytest` dependency at runtime) that discovers `test_*` functions and reports pass/fail with timings - written to demonstrate understanding of what a test runner actually does, not to replace `pytest` (`pytest test_golf_app_v8.py` runs the same file).
* 4 OCR tests need the `tesseract` binary installed and fail if it isn't, rather than falsely passing.
* OCR tests run against a temp copy of `data/fermoy_rounds.csv`, and fail if the real file is modified.

### Tier 2: Playwright E2E Suite (`test_playwright_e2e.py`)
* Uses `pytest-playwright` against a running instance of the app (Chromium by default; `pytest --browser webkit` also works since Playwright ships the driver, though only Chromium is exercised routinely here).
* Verifies the header/title, tab switching, the course dropdown's "Limited Data Mode" banner, hole selection, and the upload dropzone.

### Tier 3: Autonomous AI QA Agent (`qa_agent.py`)
* Given a plain-English goal (e.g. "explore both tabs and check the dropdowns update correctly"), the agent loops: call the Claude API with a fixed tool set → execute whichever tool it picks against a real Playwright browser → feed the result back → repeat until it calls `finish` or hits a step budget.
* Tools: `navigate`, `snapshot` (reads the live DOM instead of relying on hardcoded IDs), `click`, `get_text`, `screenshot`, `report_defect`, `finish`.
* It's a bounded `for` loop calling `client.messages.create()` directly each turn - no `tool_runner`, no agent framework - so every step of the control flow is something I can explain and defend, not a black box.
* Every run writes `reports/qa_agent_run_<timestamp>/report.md` with the goal, the full tool-call transcript, any defects logged, and the screenshots taken as evidence.

---

## 🐞 Defect Reports

Bugs found while testing this app are written up in [`docs/defects/`](docs/defects/):

* [DEF-001](docs/defects/DEF-001-ocr-silent-overwrite.md): unreadable scorecard uploads were saved as made-up par rounds, overwriting the real round for that date and reporting success. Found through a false-passing unit test. Fixed red/green, and the buggy version is kept at tag `demo/ocr-silent-overwrite` for reproduction.
* [DEF-002](docs/defects/DEF-002-hole15-par-mismatch.md): Hole 15's par/index disagrees depending which UI component you look at, because the app carries two hardcoded descriptions of Fermoy's holes that were never kept in sync. Found by `qa_agent.py`'s autonomous exploration (Tier 3) - the first defect this project's own QA agent has found unprompted. Left intentionally unfixed as a reproducible agent-found-it demo, at tag `demo/hole15-par-mismatch`.
* [DEF-003](docs/defects/DEF-003-hardcoded-fermoy-stats.md): Fermoy's "real data" summary cards (rounds tracked, avg score, best/worst hole, overall Strokes Gained) were hardcoded and never actually read `data/fermoy_rounds.csv`, unlike the hole-by-hole chart right below them. Fixed by deriving all five from the real CSV; also corrected the Strokes Gained calculation itself (it was labeled "vs 5 HCP" but computed vs scratch) and Fermoy's hole metadata against a real scorecard.

---

## 📂 Project Structure

```
back_in_bounds/
├── golf_app_v8.py              # Main Plotly Dash dashboard & OCR callback server
├── export_to_sqlite.py         # CSV -> SQLite sync
├── golf_analysis.ipynb         # Scratch notebook (date-cleaning prototyping)
├── run_tests_v8.py             # Hand-rolled CLI test runner
├── test_golf_app_v8.py         # Unit + Dash callback test suite
├── test_playwright_e2e.py      # Playwright E2E browser suite
├── qa_agent.py                 # Autonomous AI QA agent (manual Claude tool-use loop)
├── docs/defects/               # Defect reports with evidence
├── data/
│   ├── fermoy_rounds.csv       # Hole-by-hole round telemetry
│   ├── Launch Monitor Data.csv # Launch monitor shot telemetry
│   └── analytics.db            # SQLite database (generated by export_to_sqlite.py)
├── reports/                    # qa_agent.py run output (generated, gitignored)
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Install

```bash
git clone https://github.com/colinjpaul/back_in_bounds.git
cd back_in_bounds
pip install -r requirements.txt
playwright install chromium
```

### 2. Run the app

```bash
python golf_app_v8.py
```
Open `http://127.0.0.1:8050`.

### 3. Run the test suites

```bash
python run_tests_v8.py            # Tier 1: fast unit/callback suite
pytest test_golf_app_v8.py -v     # same suite via real pytest
pytest test_playwright_e2e.py -v  # Tier 2: needs the app running (step 2)
```

### 4. Run the AI QA agent

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python qa_agent.py --headed       # needs the app running (step 2)
```
Runs headless by default; pass `--headed` to watch the browser live. `--goal "..."` sets what to explore, `--max-steps N` caps the tool-call budget. Costs a small amount of Claude API usage per run.

### 5. Sync data to SQLite

```bash
python export_to_sqlite.py
```

---

## 🛠 Tech Stack

* **Language**: Python 3.12
* **Web Framework**: Plotly Dash, Flask
* **Data Processing**: Pandas, NumPy, Statsmodels
* **OCR**: PyTesseract, Pillow (+ the system `tesseract` binary)
* **Database**: SQLite3
* **Testing**: Pytest, Playwright (`pytest-playwright`)
* **AI Agent**: Anthropic Claude API (`anthropic` Python SDK), manual tool-use loop

---

## 👨‍💻 Author

**Colin Paul** — *Senior QA Lead & SDET*
* 📍 Cork, Ireland
* 💼 **25+ Years Software Quality Experience** (IBM, Qumas, Dell EMC, Trellix)
* 🌐 **Live App**: [Back in Bounds on Render](https://back-in-bounds.onrender.com)
* 🐙 **GitHub**: [github.com/colinjpaul](https://github.com/colinjpaul)
* 📧 **Contact**: colinpaul@gmail.com
