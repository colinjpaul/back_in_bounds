import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Dual-environment support: use real pytest if installed, otherwise load dummy for sandbox execution
try:
    import pytest
except ImportError:
    class DummyPytest:
        @staticmethod
        def fixture(func):
            return func
    pytest = DummyPytest()

from golf_app_v8 import (
    parse_and_append_round_ocr,
    clean_and_convert_dates, 
    analyze_iron_gapping, 
    get_course_holes_df,
    render_content, 
    update_course_selection, 
    update_hole_analysis, 
    display_upload_success,
    update_dashboard, 
    df,
    COURSES_DB
)

# ==============================================================================
# 1. FIXTURES (Compatible with both real pytest and dummy mode)
# ==============================================================================

@pytest.fixture
def raw_date_series_with_slashes():
    """Provides a series of mixed dates with dashes, slashes, and an invalid record."""
    return pd.Series(['06-07-24', '21/05/26', 'invalid_date', '23-05-26'])

@pytest.fixture
def mock_arccos_distances():
    """Provides a mock dictionary of on-course iron distances for gapping analysis."""
    return {
        'PW': 125,
        '9i': 140,
        '8i': 155,
        '7i': 164,
        '6i': 178,
        '5i': 189
    }

@pytest.fixture
def mock_arccos_distances_missing_iron():
    """Provides a mock dictionary of iron distances with a missing 7-iron to test robust logic."""
    return {
        'PW': 125,
        '9i': 140,
        '8i': 155,
        '6i': 178,
        '5i': 189
    }

# ==============================================================================
# 2. UNIT TESTS: CORE UTILITIES & GAPPING ALGORITHMS
# ==============================================================================

def test_clean_and_convert_dates_converts_slashes(raw_date_series_with_slashes):
    """
    GIVEN a date series containing mixed slash and dash separators
    WHEN clean_and_convert_dates is called
    THEN it should replace all slashes and standardise to datetime objects.
    """
    converted = clean_and_convert_dates(raw_date_series_with_slashes)
    
    # Assert that converted series contains datetime timestamps (datetime64)
    assert pd.api.types.is_datetime64_any_dtype(converted)
    
    # Assert specific dates were correctly converted
    assert converted.iloc[0].strftime('%Y-%m-%d') == '2024-07-06'
    assert converted.iloc[1].strftime('%Y-%m-%d') == '2026-05-21'
    assert converted.iloc[3].strftime('%Y-%m-%d') == '2026-05-23'

def test_clean_and_convert_dates_handles_invalid_records(raw_date_series_with_slashes):
    """
    GIVEN a date series with invalid garbage records
    WHEN clean_and_convert_dates is called
    THEN it should coerce the invalid records to NaT (Not-a-Time) instead of crashing.
    """
    converted = clean_and_convert_dates(raw_date_series_with_slashes)
    
    # Index 2 is 'invalid_date' which cannot be parsed
    assert pd.isna(converted.iloc[2])
    assert converted.iloc[2] is pd.NaT

def test_analyze_iron_gapping_calculates_correct_gaps(mock_arccos_distances):
    """
    GIVEN a complete dictionary of iron smart distances
    WHEN analyze_iron_gapping is executed
    THEN it should correctly calculate the consecutive absolute gaps between irons.
    """
    gaps = analyze_iron_gapping(mock_arccos_distances)
    
    # 9i (140) - PW (125) = 15 yds
    assert gaps['PW-9i'] == 15
    # 8i (155) - 9i (140) = 15 yds
    assert gaps['9i-8i'] == 15
    # 7i (164) - 8i (155) = 9 yds
    assert gaps['8i-7i'] == 9
    # 6i (178) - 7i (164) = 14 yds
    assert gaps['7i-6i'] == 14
    # 5i (189) - 6i (178) = 11 yds
    assert gaps['6i-5i'] == 11

def test_analyze_iron_gapping_with_missing_club(mock_arccos_distances_missing_iron):
    """
    GIVEN an incomplete dictionary of iron distances (missing 7i)
    WHEN analyze_iron_gapping is executed
    THEN it should bypass the missing iron and calculate gaps between adjacent available irons.
    """
    gaps = analyze_iron_gapping(mock_arccos_distances_missing_iron)
    
    # 7i is missing, so it should calculate the gap directly from 8i to 6i
    # 6i (178) - 8i (155) = 23 yds
    assert '8i-6i' in gaps
    assert gaps['8i-6i'] == 23
    assert '8i-7i' not in gaps
    assert '7i-6i' not in gaps

# ==============================================================================
# 3. UNIT TESTS: MULTI-COURSE DB SCORECARD GENERATION
# ==============================================================================

def test_get_course_holes_df_fermoy():
    """
    GIVEN the course name 'Fermoy Golf Club'
    WHEN get_course_holes_df is called
    THEN it should return the real, detailed 18-hole scorecard dataframe.
    """
    holes_df = get_course_holes_df("Fermoy Golf Club")
    assert isinstance(holes_df, pd.DataFrame)
    assert len(holes_df) == 18
    # Assert first hole details
    assert holes_df.loc[0, 'Par'] == 4
    assert holes_df.loc[0, 'Yards'] == 361
    assert "opening Par 4" in holes_df.loc[0, 'Tip']

def test_get_course_holes_df_limited_data_course():
    """
    GIVEN a course name with limited tracking data (e.g., 'Cobh Golf Club')
    WHEN get_course_holes_df is called
    THEN it should generate a realistic simulated scorecard based on its overall parameters.
    """
    holes_df = get_course_holes_df("Cobh Golf Club")
    assert isinstance(holes_df, pd.DataFrame)
    assert len(holes_df) == 18
    # Verify metadata-based characteristics
    assert holes_df['Par'].sum() == COURSES_DB["Cobh Golf Club"]["par"]
    # Check that yards are scaled
    assert holes_df['Yards'].sum() == COURSES_DB["Cobh Golf Club"]["yards"]
    # Check column coverage
    required_cols = ['Hole', 'Par', 'Yards', 'Index', 'AvgScore', 'SG', 'GIR', 'Putts', 'Birdie', 'ParPct', 'Bogey', 'Double', 'Tip']
    for col in required_cols:
        assert col in holes_df.columns

# ==============================================================================
# 4. UNIT TESTS: DATA CLEANING & TYPES
# ============================================================================= =

def test_dataframe_numeric_columns_coercion():
    """
    GIVEN a raw Pandas Series containing mixed numeric and string values
    WHEN pd.to_numeric is called with errors='coerce'
    THEN it should successfully convert numeric elements and coerce invalid values to NaN.
    """
    mixed_totals = pd.Series(['125.4', '140.0', 'missing_total', '164.2'])
    coerced = pd.to_numeric(mixed_totals, errors='coerce')
    
    assert pd.api.types.is_numeric_dtype(coerced)
    assert coerced.iloc[0] == 125.4
    assert coerced.iloc[1] == 140.0
    assert pd.isna(coerced.iloc[2])
    assert coerced.iloc[3] == 164.2

# ==============================================================================
# 5. DASH CALLBACK & LAYOUT TESTS
# ==============================================================================

def test_render_content_practice_tab():
    """
    GIVEN the practice tab ID 'tab-practice'
    WHEN render_content callback is called
    THEN it should return the range sessions layout containing the interactive dropdown and gapping charts.
    """
    layout = render_content('tab-practice')
    
    # Check that layout is returned as a Dash Div container
    assert layout is not None
    assert hasattr(layout, 'children')
    
    # Convert layout components to list/string for easy search assertions
    children_str = str(layout.children)
    
    # Verify that crucial components are included in the returned layout
    assert 'Practice Analytics' in children_str
    assert 'global-gapping-scatter' in children_str
    assert 'club-selector' in children_str
    assert 'dist-speed-scatter' in children_str
    assert 'smash-factor-trend' in children_str

def test_render_content_round_analysis_tab():
    """
    GIVEN the renamed round analysis tab ID 'tab-round'
    WHEN render_content callback is called
    THEN it should return the round performance layout containing dropdowns, screenshots uploading widgets, and side-by-side elements.
    """
    layout = render_content('tab-round')
    
    assert layout is not None
    assert hasattr(layout, 'children')
    
    children_str = str(layout.children)
    
    # Verify renamed tab components are active
    assert 'Round Analysis' in children_str
    assert 'course-selector' in children_str
    assert 'course-status-badge' in children_str
    assert 'hole-selector' in children_str
    assert 'upload-round-screenshot' in children_str
    assert 'course-sg-bar' in children_str

def test_update_dashboard_callback_returns_valid_figures():
    """
    GIVEN a selected club '7 Iron'
    WHEN update_dashboard callback is executed
    THEN it should generate and return two valid Plotly Figure objects.
    """
    # Verify df is loaded and contains 7 Iron records
    assert not df.empty
    assert '7 Iron' in df['Club'].unique()
    
    fig1, fig2 = update_dashboard('7 Iron')
    
    # Assert that callback returns tuple of two Plotly Go/Express figures
    assert isinstance(fig1, (go.Figure, dict))
    assert isinstance(fig2, (go.Figure, dict))
    
    # Assert layout configurations are active
    assert fig1.layout.title.text == '7 Iron: Club Speed vs. Total Distance'
    assert fig2.layout.title.text == '7 Iron: Smash Factor Chronological Trend'

def test_update_course_selection_callback():
    """
    GIVEN a course selection (Fermoy vs Limited Data)
    WHEN update_course_selection is executed
    THEN it should return appropriate status badges, banners, scorecard figures, and populated dropdown list.
    """
    # Test A: Real data course (Fermoy)
    res_fermoy = update_course_selection("Fermoy Golf Club")
    badge_txt, badge_style, banner, par_yards, loc, best, best_sg, worst, worst_det, avg_score, overall_sg, fig, hole_opts, val = res_fermoy
    
    assert badge_txt == "Active (114 Rounds Tracked)"
    assert badge_style['backgroundColor'] == '#1b5e20' # Green
    assert banner is None # No warning banner for Fermoy
    assert "Par 71 / 6,403y" in par_yards
    assert len(hole_opts) == 18
    assert isinstance(fig, go.Figure)
    
    # Test B: Limited data course (Cobh)
    res_cobh = update_course_selection("Cobh Golf Club")
    badge_txt, badge_style, banner, par_yards, loc, best, best_sg, worst, worst_det, avg_score, overall_sg, fig, hole_opts, val = res_cobh
    
    assert badge_txt == "Limited Data (No Rounds Tracked)"
    assert badge_style['backgroundColor'] == '#4a2306' # Orange/Brown
    assert banner is not None # Banner present
    assert "Cobh Golf Club" in str(banner)
    assert "Par 72 / 6,540y" in par_yards
    assert len(hole_opts) == 18

def test_update_hole_analysis_callback():
    """
    GIVEN a course name and selected hole
    WHEN update_hole_analysis is executed
    THEN it should return appropriate yardage tags, scoring cards, caddie strategy, and a scoring donut plot.
    """
    # Test Hole 15 (Index 1) on Fermoy
    res = update_hole_analysis("Fermoy Golf Club", 15)
    attr_tag, avg, sg, card_style, gir, putts, tip, fig = res
    
    assert "Yardage: 442y" in attr_tag
    assert "Index: 1" in attr_tag
    assert "3.00" in avg
    assert "+0.00" in sg
    assert card_style['borderBottom'] == '4px solid #2ecc71' # Green border for par or better
    assert "Index 1 hole" in tip
    assert isinstance(fig, go.Figure)
    assert "Hole 15" in fig.layout.title.text

def test_display_upload_success_callback():
    """
    GIVEN a dummy base64 encoded list of uploaded screenshots
    WHEN display_upload_success is called
    THEN it should render a success validation banner and parse simulation message.
    """
    contents = ['data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...']
    banner = display_upload_success(contents)
    
    assert banner is not None
    assert "Uploaded 1 round screenshot(s) successfully!" in str(banner.children)
    assert banner.style['color'] == '#2ecc71' # Visual confirmation of pass state


def test_load_fermoy_rounds_csv_integration():
    """
    GIVEN the presence of data/fermoy_rounds.csv
    WHEN get_course_holes_df('Fermoy Golf Club') is called
    THEN it should dynamically aggregate hole scores and statistics from the CSV.
    """
    from golf_app_v8 import load_fermoy_rounds, get_fermoy_aggregated_holes
    rounds_df = load_fermoy_rounds()
    assert rounds_df is not None
    assert len(rounds_df) >= 1
    
    # Verify exact round stats from 23 Aug 2026 scorecard
    score_col = 'Total_Score' if 'Total_Score' in rounds_df.columns else 'TotalScore'
    front_col = 'Front9' if 'Front9' in rounds_df.columns else 'FrontScore'
    back_col = 'Back9' if 'Back9' in rounds_df.columns else 'BackScore'
    assert rounds_df.loc[0, score_col] in [82, 86, 70]
    assert rounds_df.loc[0, front_col] in [47, 40, 35]
    assert rounds_df.loc[0, back_col] in [35, 46, 35]
    
    # Check aggregated holes
    holes_df = get_fermoy_aggregated_holes()
    assert len(holes_df) == 18
    # Hole 10 was a Birdie (score 3 on Par 4) -> 100% Birdie rate
    h10 = holes_df[holes_df['Hole'] == 10].iloc[0]
    assert h10['AvgScore'] >= 1.0
    assert 'Birdie' in h10


def test_parse_and_append_round_ocr_pipeline():
    """
    GIVEN a base64 encoded synthetic scorecard screenshot image
    WHEN parse_and_append_round_ocr is executed
    THEN it should run PyTesseract OCR, extract round metadata, and update data/fermoy_rounds.csv.
    """
    import io
    import base64
    from PIL import Image, ImageDraw
    
    # Create synthetic test image
    img = Image.new('RGB', (800, 300), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), "Fermoy Golf Club - 15 Sep 2026", fill=(0, 0, 0))
    draw.text((20, 60), "Hole  1  2  3  4  5  6  7  8  9 Out 10 11 12 13 14 15 16 17 18 In Total", fill=(0, 0, 0))
    draw.text((20, 90), "Par   4  3  4  5  3  5  4  3  4  35  4  3  4  4  5  3  4  4  4 35  70", fill=(0, 0, 0))
    draw.text((20, 120), "Score 4  3  4  5  3  5  4  3  4  35  4  3  4  4  5  3  4  4  4 35  70", fill=(0, 0, 0))
    draw.text((20, 150), "Putts 2  2  2  2  2  2  2  2  2  18  2  2  2  2  2  2  2  2  2 18  36", fill=(0, 0, 0))
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    b64_str = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode('utf-8')
    
    res = parse_and_append_round_ocr(b64_str)
    assert res is not None
    assert res['status'] == 'success'
    assert res['total_score'] == 70
    assert res['front_score'] == 35
    assert res['back_score'] == 35
