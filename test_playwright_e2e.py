"""
==============================================================================
BACK IN BOUNDS - PLAYWRIGHT E2E BROWSER AUTOMATION TEST SUITE
==============================================================================
Framework: Playwright (Python API) + Pytest
Target: Running Dash Web Application (http://127.0.0.1:8050)

To run on your local Mac:
  1. pip install pytest-playwright
  2. playwright install
  3. python golf_app_v5.py (in Terminal 1)
  4. pytest test_playwright_e2e.py -v (in Terminal 2)
==============================================================================
"""

import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://127.0.0.1:8050"


def test_app_header_and_title(page: Page):
    """
    GIVEN the Dash application is running
    WHEN a user navigates to the base URL
    THEN the page title and header banner should display 'Back in Bounds'.
    """
    page.goto(BASE_URL)

    # Verify Page Title
    expect(page).to_have_title("Dash")

    # Verify Main Navigation Header
    header = page.locator("#main-header h1")
    expect(header).to_be_visible()
    expect(header).to_have_text("Back in Bounds: Golf Performance Analytics")


def test_tab_navigation(page: Page):
    """
    GIVEN the app opens on the default 'Round Analysis' tab
    WHEN the user clicks the 'Range Sessions' tab
    THEN the DOM should update to show practice analytics and club deep dive.
    """
    page.goto(BASE_URL)

    # Assert 'Round Analysis' is active by default
    round_heading = page.locator("h2", has_text="Round Analysis")
    expect(round_heading).to_be_visible()

    # Click 'Range Sessions' Tab
    page.click("#tab-practice-btn")

    # Verify DOM updates to show Launch Monitor analytics
    practice_heading = page.locator("h2", has_text="Practice Analytics")
    expect(practice_heading).to_be_visible()

    # Verify single-club dropdown is rendered
    expect(page.locator("#club-selector")).to_be_visible()


def test_course_selector_interaction(page: Page):
    """
    GIVEN the Round Analysis tab
    WHEN the user selects 'Cobh Golf Club' from the course dropdown
    THEN the status badge should update to 'Limited Data Mode' and display a warning banner.
    """
    page.goto(BASE_URL)

    # Click Course Selector Dropdown
    page.click("#course-selector")

    # Select Cobh Golf Club option
    page.click("text=Cobh Golf Club")

    # Verify Status Badge updates
    badge = page.locator("#course-status-badge")
    expect(badge).to_contain_text("Limited Data")

    # Verify Warning Banner is rendered in DOM
    banner = page.locator("#limited-data-banner-container")
    expect(banner).to_contain_text("No Arccos round files have been uploaded for Cobh Golf Club")


def test_hole_selector_and_caddie_strategy(page: Page):
    """
    GIVEN Fermoy Golf Club is selected
    WHEN the user selects Hole 15 from the dropdown
    THEN the metrics and caddie strategy card should update for the Index 1 hole.
    """
    page.goto(BASE_URL)

    # Select Hole 15 from hole dropdown
    page.click("#hole-selector")
    page.click("text=Hole 15")

    # Verify Caddie Strategy updates for Hole 15
    strategy_card = page.locator("#deep-dive-strategy-tip")
    expect(strategy_card).to_contain_text("Index 1 hole")


def test_screenshot_upload_widget(page: Page):
    """
    GIVEN the Round Analysis tab
    WHEN the user interacts with the drag-and-drop upload widget
    THEN the upload container should be visible and ready for file inputs.
    """
    page.goto(BASE_URL)

    # Locate the dcc.Upload dropzone
    upload_widget = page.locator("#upload-round-screenshot")
    expect(upload_widget).to_be_visible()
    expect(upload_widget).to_contain_text("Drag and Drop or Browse File")
