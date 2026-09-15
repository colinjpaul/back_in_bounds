import os
import pandas as pd
import numpy as np
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go

# ==============================================================================
# 1. CORE UTILITY & DATA CLEANING FUNCTIONS (Unit Test Targets)
# ==============================================================================

def clean_and_convert_dates(date_series):
    """
    Standardises date separators by replacing slashes with dashes and
    converts the series to datetime with robust error handling (coercing errors to NaT).
    """
    clean_series = date_series.astype(str).str.replace('/', '-', regex=False)
    return pd.to_datetime(clean_series, format='%d-%m-%y', errors='coerce')

def analyze_iron_gapping(distances_dict):
    """
    Calculates distance gaps between consecutive irons from PW to 5i.
    Returns a dictionary of gaps in yards.
    """
    ordered_irons = ['PW', '9i', '8i', '7i', '6i', '5i']
    available_irons = [club for club in ordered_irons if club in distances_dict]
    
    gaps = {}
    for i in range(1, len(available_irons)):
        shorter_club = available_irons[i-1]
        longer_club = available_irons[i]
        
        shorter_dist = distances_dict[shorter_club]
        longer_dist = distances_dict[longer_club]
        
        gaps[f"{shorter_club}-{longer_club}"] = abs(longer_dist - shorter_dist)
        
    return gaps

# ==============================================================================
# 2. AUTO-GENERATION OF MOCK LAUNCH MONITOR DATA (For stand-alone demo)
# ==============================================================================
os.makedirs('data', exist_ok=True)
csv_path = 'data/launch_mon_may21_26.csv'

if not os.path.exists(csv_path):
    # Generating realistic 10 HCP launch monitor dataset
    clubs = ['Driver', '5 Wood', '4 Iron', '5 Iron', '6 Iron', '7 Iron', '8 Iron', '9 Iron', 'PW', 'LW (58)']
    dates = ['06-07-24', '12-08-24', '15-10-24', '04-03-25', '14-05-25', '21-05-26', '23-05-26', '12-06-26', '18-07-26']
    
    base_stats = {
        'Driver': {'speed': (95, 101), 'smash': (1.42, 1.48), 'distance_mult': 2.45},
        '5 Wood': {'speed': (88, 93), 'smash': (1.38, 1.44), 'distance_mult': 2.30},
        '4 Iron': {'speed': (82, 86), 'smash': (1.33, 1.39), 'distance_mult': 2.20},
        '5 Iron': {'speed': (80, 84), 'smash': (1.31, 1.37), 'distance_mult': 2.15},
        '6 Iron': {'speed': (77, 81), 'smash': (1.29, 1.35), 'distance_mult': 2.10},
        '7 Iron': {'speed': (74, 78), 'smash': (1.27, 1.33), 'distance_mult': 2.05},
        '8 Iron': {'speed': (71, 75), 'smash': (1.25, 1.31), 'distance_mult': 2.00},
        '9 Iron': {'speed': (68, 72), 'smash': (1.23, 1.29), 'distance_mult': 1.95},
        'PW': {'speed': (65, 69), 'smash': (1.20, 1.26), 'distance_mult': 1.90},
        'LW (58)': {'speed': (60, 64), 'smash': (1.10, 1.18), 'distance_mult': 1.65}
    }
    
    data = []
    np.random.seed(42)
    for _ in range(120):
        club = np.random.choice(clubs)
        date = np.random.choice(dates)
        if np.random.rand() < 0.2:
            date = date.replace('-', '/')  # Inject occasional slashes to verify date cleaning
            
        stats = base_stats[club]
        speed = np.round(np.random.uniform(*stats['speed']), 1)
        smash = np.round(np.random.uniform(*stats['smash']), 2)
        total = np.round(speed * smash * stats['distance_mult'] * np.random.uniform(0.97, 1.03), 1)
        
        data.append({
            'Date': date,
            'Club': club,
            'Club Speed': speed,
            'Smash': smash,
            'Total': total
        })
    pd.DataFrame(data).to_csv(csv_path, index=False)

# Load and clean launch monitor data
df = pd.read_csv(csv_path)
df['Date'] = clean_and_convert_dates(df['Date'])
for col in ['Total', 'Club Speed', 'Smash']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Pre-generate global gapping scatter plot
global_fig = px.scatter(
    df.dropna(subset=['Club Speed', 'Total']),
    x='Club Speed',
    y='Total',
    color='Club',
    hover_data=['Smash', 'Date'],
    title="Bag Gapping: Club Speed vs. Total Distance (All Clubs)",
    template="plotly_dark",
    labels={'Total': 'Total Distance (yds)', 'Club Speed': 'Club Speed (mph)'}
)
global_fig.update_layout(
    margin=dict(l=40, r=40, t=50, b=40),
    plot_bgcolor='#1a1a1a',
    paper_bgcolor='#121212'
)

# ============================================================================= =
# 3. MULTI-COURSE DATABASE & SCORECARD INFRASTRUCTURE
# ============================================================================= =

COURSES_DB = {
    "Fermoy Golf Club": {
        "location": "Fermoy, County Cork",
        "par": 71,
        "yards": 6403,
        "status": "Active (114 Rounds Tracked)",
        "has_real_data": True,
        "best_holes": "Holes 4 & 16",
        "worst_hole": "Hole 15 (Index 1)",
        "avg_score": 81.3,
        "overall_sg": -5.0
    },
    "Castlemartyr Golf Club": {
        "location": "Cork, County Cork",
        "par": 72,
        "yards": 6790,
        "status": "Limited Data (No Rounds Tracked)",
        "has_real_data": False,
        "best_holes": "Hole 9 (Par 5)",
        "worst_hole": "Hole 4 (Index 1)",
        "avg_score": 83.5,
        "overall_sg": -6.5
    },
    "Cobh Golf Club": {
        "location": "Cobh, County Cork",
        "par": 72,
        "yards": 6540,
        "status": "Limited Data (No Rounds Tracked)",
        "has_real_data": False,
        "best_holes": "Hole 10 (Par 4)",
        "worst_hole": "Hole 7 (Index 1)",
        "avg_score": 84.1,
        "overall_sg": -7.1
    },
    "Cork Golf Club": {
        "location": "Little Island, County Cork",
        "par": 72,
        "yards": 6445,
        "status": "Limited Data (No Rounds Tracked)",
        "has_real_data": False,
        "best_holes": "Hole 12 (Par 3)",
        "worst_hole": "Hole 5 (Index 1)",
        "avg_score": 85.0,
        "overall_sg": -8.0
    },
    "Fota Island Golf Club": {
        "location": "Deerpark, Fota Island, County Cork",
        "par": 71,
        "yards": 6588,
        "status": "Limited Data (No Rounds Tracked)",
        "has_real_data": False,
        "best_holes": "Hole 6 (Par 4)",
        "worst_hole": "Hole 11 (Index 1)",
        "avg_score": 84.5,
        "overall_sg": -7.5
    },
    "Gold Coast Golf Course": {
        "location": "Dungarvan, County Waterford",
        "par": 72,
        "yards": 6410,
        "status": "Limited Data (No Rounds Tracked)",
        "has_real_data": False,
        "best_holes": "Hole 2 (Par 5)",
        "worst_hole": "Hole 14 (Index 1)",
        "avg_score": 83.0,
        "overall_sg": -6.0
    },
    "Killarney Golf & Fishing Club": {
        "location": "Killeen, Killarney, County Kerry",
        "par": 72,
        "yards": 6525,
        "status": "Limited Data (No Rounds Tracked)",
        "has_real_data": False,
        "best_holes": "Hole 18 (Par 4)",
        "worst_hole": "Hole 3 (Index 1)",
        "avg_score": 83.8,
        "overall_sg": -6.8
    },
    "Lismore Golf Club": {
        "location": "Lismore, County Waterford",
        "par": 69,
        "yards": 5680,
        "status": "Limited Data (No Rounds Tracked)",
        "has_real_data": False,
        "best_holes": "Hole 5 (Par 3)",
        "worst_hole": "Hole 8 (Index 1)",
        "avg_score": 79.5,
        "overall_sg": -5.5
    },
    "Mahon Golf Club": {
        "location": "Ted McCarthy Course, Blackrock, County Cork",
        "par": 70,
        "yards": 5690,
        "status": "Limited Data (No Rounds Tracked)",
        "has_real_data": False,
        "best_holes": "Hole 17 (Par 3)",
        "worst_hole": "Hole 6 (Index 1)",
        "avg_score": 81.0,
        "overall_sg": -6.0
    },
    "Mallow Golf Club": {
        "location": "Mallow, County Cork",
        "par": 72,
        "yards": 6340,
        "status": "Limited Data (No Rounds Tracked)",
        "has_real_data": False,
        "best_holes": "Hole 15 (Par 5)",
        "worst_hole": "Hole 4 (Index 1)",
        "avg_score": 84.0,
        "overall_sg": -7.0
    },
    "Mitchelstown Golf Club": {
        "location": "Mitchelstown, County Cork",
        "par": 71,
        "yards": 5990,
        "status": "Limited Data (No Rounds Tracked)",
        "has_real_data": False,
        "best_holes": "Hole 8 (Par 3)",
        "worst_hole": "Hole 13 (Index 1)",
        "avg_score": 82.5,
        "overall_sg": -6.5
    },
    "Monkstown Golf Club": {
        "location": "Monkstown, County Cork",
        "par": 70,
        "yards": 6010,
        "status": "Limited Data (No Rounds Tracked)",
        "has_real_data": False,
        "best_holes": "Hole 3 (Par 4)",
        "worst_hole": "Hole 12 (Index 1)",
        "avg_score": 81.8,
        "overall_sg": -6.8
    },
    "Mount Juliet Golf Club": {
        "location": "Thomastown, County Kilkenny",
        "par": 72,
        "yards": 7300,
        "status": "Limited Data (No Rounds Tracked)",
        "has_real_data": False,
        "best_holes": "Hole 10 (Par 5)",
        "worst_hole": "Hole 11 (Index 1)",
        "avg_score": 86.5,
        "overall_sg": -9.5
    },
    "The Heritage Golf Course": {
        "location": "Killenard, County Laois",
        "par": 72,
        "yards": 7319,
        "status": "Limited Data (No Rounds Tracked)",
        "has_real_data": False,
        "best_holes": "Hole 9 (Par 4)",
        "worst_hole": "Hole 16 (Index 1)",
        "avg_score": 87.0,
        "overall_sg": -10.0
    },
    "Water Rock Golf Course": {
        "location": "Midleton, County Cork",
        "par": 70,
        "yards": 5890,
        "status": "Limited Data (No Rounds Tracked)",
        "has_real_data": False,
        "best_holes": "Hole 7 (Par 4)",
        "worst_hole": "Hole 5 (Index 1)",
        "avg_score": 81.5,
        "overall_sg": -6.5
    },
    "Youghal Golf Club": {
        "location": "Youghal, County Cork",
        "par": 71,
        "yards": 5950,
        "status": "Limited Data (No Rounds Tracked)",
        "has_real_data": False,
        "best_holes": "Hole 14 (Par 3)",
        "worst_hole": "Hole 9 (Index 1)",
        "avg_score": 82.2,
        "overall_sg": -6.2
    }
}

# Real Fermoy detailed data
fermoy_holes_raw = [
    {"Hole": 1, "Par": 4, "Yards": 361, "Index": 12, "AvgScore": 4.35, "SG": -0.15, "GIR": 35, "Putts": 1.8, "Birdie": 5, "ParPct": 55, "Bogey": 35, "Double": 5, "Tip": "A gentle opening Par 4. Favor the right side of the fairway as everything slopes left. A solid drive leaves a short iron into a flat green." },
    {"Hole": 2, "Par": 4, "Yards": 388, "Index": 10, "AvgScore": 4.50, "SG": -0.25, "GIR": 25, "Putts": 1.9, "Birdie": 5, "ParPct": 45, "Bogey": 40, "Double": 10, "Tip": "Blind tee shot. Aim at the white marker post. The approach shot plays slightly downhill, so take one less club if the wind is down." },
    {"Hole": 3, "Par": 4, "Yards": 437, "Index": 2, "AvgScore": 5.15, "SG": -0.60, "GIR": 10, "Putts": 2.0, "Birdie": 0, "ParPct": 20, "Bogey": 50, "Double": 30, "Tip": "A monster Par 4 playing uphill. GIR is extremely rare here. Strategy: Treat this as a three-shot hole. Lay up to your favorite wedge distance and rely on your strong short game (+0.8 SG) to scramble for par." },
    {"Hole": 4, "Par": 3, "Yards": 143, "Index": 18, "AvgScore": 3.15, "SG": 0.05, "GIR": 55, "Putts": 1.7, "Birdie": 15, "ParPct": 65, "Bogey": 15, "Double": 5, "Tip": "Your best performing hole! A short Par 3 with a large green. Club selection is key; trust your PW (125 yds) or 9i if playing into a breeze. Avoid going long at all costs." },
    {"Hole": 5, "Par": 4, "Yards": 396, "Index": 8, "AvgScore": 4.65, "SG": -0.35, "GIR": 20, "Putts": 1.8, "Birdie": 5, "ParPct": 40, "Bogey": 45, "Double": 10, "Tip": "Overshooting the green here leaves a very tricky chip. Play to the front of the green and let your putter do the work." },
    {"Hole": 6, "Par": 4, "Yards": 350, "Index": 14, "AvgScore": 4.40, "SG": -0.20, "GIR": 40, "Putts": 1.8, "Birdie": 10, "ParPct": 50, "Bogey": 30, "Double": 10, "Tip": "A shorter Par 4, but tight off the tee. Ditch the driver and hit a 5-wood or 4-iron to guarantee finding the fairway and giving yourself a clean wedge look." },
    {"Hole": 7, "Par": 5, "Yards": 513, "Index": 4, "AvgScore": 5.25, "SG": -0.15, "GIR": 30, "Putts": 1.9, "Birdie": 15, "ParPct": 50, "Bogey": 25, "Double": 10, "Tip": "Double dogleg Par 5. The second shot must be positioned on the right side of the fairway to have any view of the green for your third." },
    {"Hole": 8, "Par": 3, "Yards": 168, "Index": 16, "AvgScore": 3.45, "SG": -0.20, "GIR": 40, "Putts": 1.8, "Birdie": 5, "ParPct": 55, "Bogey": 35, "Double": 5, "Tip": "A tricky Par 3 playing to an elevated green. Take one extra club (7-iron instead of 8-iron) to clear the front bunkers." },
    {"Hole": 9, "Par": 4, "Yards": 411, "Index": 6, "AvgScore": 4.75, "SG": -0.40, "GIR": 15, "Putts": 1.9, "Birdie": 0, "ParPct": 35, "Bogey": 55, "Double": 10, "Tip": "Tough finishing hole on the front nine. Aim your drive down the left-center. The green has a severe slope from back to front—stay below the hole." },
    {"Hole": 10, "Par": 4, "Yards": 355, "Index": 15, "AvgScore": 4.35, "SG": -0.15, "GIR": 35, "Putts": 1.8, "Birdie": 10, "ParPct": 50, "Bogey": 35, "Double": 5, "Tip": "An excellent scoring opportunity. A good drive leaves a short wedge. Guard against getting lazy with your wedge distance control." },
    {"Hole": 11, "Par": 4, "Yards": 390, "Index": 9, "AvgScore": 4.60, "SG": -0.30, "GIR": 20, "Putts": 1.8, "Birdie": 5, "ParPct": 45, "Bogey": 40, "Double": 10, "Tip": "Aim for the right side of the fairway to open up the green. The green is narrow and heavily guarded by trees on the left." },
    {"Hole": 12, "Par": 3, "Yards": 198, "Index": 7, "AvgScore": 3.85, "SG": -0.45, "GIR": 15, "Putts": 1.9, "Birdie": 0, "ParPct": 35, "Bogey": 50, "Double": 15, "Tip": "A long, daunting Par 3. Your 5-iron or 5-wood is the play here. If you miss, miss short-right to leave an easy chip." },
    {"Hole": 13, "Par": 4, "Yards": 382, "Index": 11, "AvgScore": 4.55, "SG": -0.25, "GIR": 25, "Putts": 1.8, "Birdie": 5, "ParPct": 45, "Bogey": 45, "Double": 5, "Tip": "Slight dogleg right. A drive over the corner of the trees cuts off significant yardage, but safety lies down the left center." },
    {"Hole": 14, "Par": 4, "Yards": 404, "Index": 3, "AvgScore": 4.90, "SG": -0.50, "GIR": 15, "Putts": 1.9, "Birdie": 0, "ParPct": 30, "Bogey": 55, "Double": 15, "Tip": "Strong Par 4. The approach shot is uphill to a multi-tiered green. Take an extra club to ensure you reach the correct tier." },
    {"Hole": 15, "Par": 4, "Yards": 442, "Index": 1, "AvgScore": 5.25, "SG": -0.65, "GIR": 5, "Putts": 2.0, "Birdie": 0, "ParPct": 15, "Bogey": 50, "Double": 35, "Tip": "The Index 1 hole and your largest leakage on the course. At 442 yards, it's a par 5 for most. Strategy: Lay up off the tee or on your second shot to 60 yards. Play for a 5 and avoid the card-wrecking double bogeys." },
    {"Hole": 16, "Par": 5, "Yards": 532, "Index": 13, "AvgScore": 5.10, "SG": 0.05, "GIR": 45, "Putts": 1.8, "Birdie": 20, "ParPct": 55, "Bogey": 20, "Double": 5, "Tip": "Your second best performing hole! An authentic par 5 where your distance off the tee pays dividends. A good drive gives you a real chance to reach or get close in two." },
    {"Hole": 17, "Par": 3, "Yards": 151, "Index": 17, "AvgScore": 3.35, "SG": -0.15, "GIR": 45, "Putts": 1.8, "Birdie": 10, "ParPct": 55, "Bogey": 30, "Double": 5, "Tip": "A scenic Par 3 over a valley. Wind can be deceptive here. Throw some grass in the air to check the breeze and trust your 8 or 9-iron yardage." },
    {"Hole": 18, "Par": 4, "Yards": 382, "Index": 5, "AvgScore": 4.80, "SG": -0.45, "GIR": 20, "Putts": 1.9, "Birdie": 5, "ParPct": 35, "Bogey": 45, "Double": 15, "Tip": "Tough finishing hole playing back towards the clubhouse. Aim your tee shot left of the fairway bunker. The green is well-protected by deep greenside bunkers." }
]


# Load or initialize Fermoy rounds CSV database
FERMOY_CSV_PATH = 'data/fermoy_rounds.csv'

def load_fermoy_rounds():
    """
    Loads Fermoy rounds from CSV if present, otherwise returns default structure.
    Calculates per-hole averages, GIR%, Putts, and scoring distributions.
    """
    if os.path.exists(FERMOY_CSV_PATH):
        try:
            return pd.read_csv(FERMOY_CSV_PATH)
        except Exception:
            pass
    return None

def get_fermoy_aggregated_holes():
    """
    Aggregates logged Fermoy rounds to produce hole-by-hole stats.
    Falls back to fermoy_holes_raw if no CSV is available.
    """
    rounds_df = load_fermoy_rounds()
    if rounds_df is None or len(rounds_df) == 0:
        return pd.DataFrame(fermoy_holes_raw)
    
    # Process rounds_df to compute aggregated stats per hole
    holes_data = []
    # Base layout metadata for Fermoy
    fermoy_base_pars = [4, 3, 4, 5, 3, 5, 4, 3, 4, 4, 3, 4, 4, 5, 3, 4, 4, 4]
    fermoy_base_yards = [361, 388, 437, 143, 396, 350, 513, 168, 411, 355, 390, 198, 382, 404, 442, 532, 151, 382]
    fermoy_base_indices = [12, 10, 2, 18, 8, 14, 4, 16, 6, 15, 9, 7, 11, 3, 1, 13, 17, 5]
    
    num_rounds = len(rounds_df)
    
    for h in range(1, 19):
        par = fermoy_base_pars[h-1]
        yards = fermoy_base_yards[h-1]
        idx = fermoy_base_indices[h-1]
        
        scores = rounds_df[f'H{h}_Score'] if f'H{h}_Score' in rounds_df.columns else [par]
        girs = rounds_df[f'H{h}_GIR'] if f'H{h}_GIR' in rounds_df.columns else [0]
        putts = rounds_df[f'H{h}_Putts'] if f'H{h}_Putts' in rounds_df.columns else [2]
        
        avg_score = float(np.mean(scores))
        avg_gir = float(np.mean(girs)) * 100
        avg_putts = float(np.mean(putts))
        sg = np.round(par - avg_score, 2)
        
        # Calculate scoring distribution
        birdies = sum(s <= par - 1 for s in scores)
        pars_cnt = sum(s == par for s in scores)
        bogeys = sum(s == par + 1 for s in scores)
        doubles = sum(s >= par + 2 for s in scores)
        
        birdie_pct = int(np.round(birdies * 100 / num_rounds))
        par_pct = int(np.round(pars_cnt * 100 / num_rounds))
        bogey_pct = int(np.round(bogeys * 100 / num_rounds))
        double_pct = int(np.round(doubles * 100 / num_rounds))
        
        # Pull original caddie tip from base raw if available
        base_tip = fermoy_holes_raw[h-1]['Tip'] if h-1 < len(fermoy_holes_raw) else "Focus on fairway positioning and smooth green transition."
        
        holes_data.append({
            "Hole": h,
            "Par": par,
            "Yards": yards,
            "Index": idx,
            "AvgScore": np.round(avg_score, 2),
            "SG": sg,
            "GIR": int(np.round(avg_gir)),
            "Putts": np.round(avg_putts, 2),
            "Birdie": birdie_pct,
            "ParPct": par_pct,
            "Bogey": bogey_pct,
            "Double": double_pct,
            "Tip": base_tip
        })
        
    return pd.DataFrame(holes_data)

def get_course_holes_df(course_name):
    """
    Returns the dataframe of 18 holes for the specified course.
    If the course is Fermoy Golf Club, returns real data.
    Otherwise, returns dynamically estimated scorecard baseline for a 10 HCP on that course.
    """
    if course_name == "Fermoy Golf Club" or course_name not in COURSES_DB:
        return get_fermoy_aggregated_holes()
    
    metadata = COURSES_DB[course_name]
    par = metadata["par"]
    total_yards = metadata["yards"]
    
    # Generate 18 holes
    np.random.seed(sum(map(ord, course_name)))  # Consistent seed based on course name
    holes = []
    
    # Distribute pars based on course total par
    pars = [4]*18
    # Par 3 holes
    par3_indices = [3, 7, 11, 16] # 0-indexed: holes 4, 8, 12, 17
    for idx in par3_indices:
        pars[idx] = 3
    # Par 5 holes
    par5_indices = [6, 15] # 0-indexed: holes 7, 16
    for idx in par5_indices:
        pars[idx] = 5
        
    # Adjust total par if needed
    if par == 72:
        pars[2] = 5 # hole 3
        pars[10] = 5 # hole 11
    elif par == 70:
        pars[4] = 3 # hole 5
    elif par == 69:
        pars[4] = 3 # hole 5
        pars[14] = 3 # hole 15
        
    # Stroke indices (randomized permutation of 1 to 18)
    indices = list(range(1, 19))
    np.random.shuffle(indices)
    
    # Strict scaling of yardage so that sum of holes is EXACTLY total_yards
    raw_yards = []
    for h in range(1, 19):
        hole_par = pars[h-1]
        if hole_par == 3:
            raw_yards.append(np.random.uniform(130, 190))
        elif hole_par == 5:
            raw_yards.append(np.random.uniform(485, 545))
        else:
            raw_yards.append(np.random.uniform(340, 415))
            
    sum_raw = sum(raw_yards)
    scaled_yards = [int(np.round(y * total_yards / sum_raw)) for y in raw_yards]
    
    # Adjust exact sum rounding discrepancy
    diff = total_yards - sum(scaled_yards)
    if diff != 0:
        longest_idx = scaled_yards.index(max(scaled_yards))
        scaled_yards[longest_idx] += diff
    
    for h in range(1, 19):
        hole_par = pars[h-1]
        y = scaled_yards[h-1]
        h_idx = indices[h-1]
        difficulty_weight = (19 - h_idx) / 18.0 # Higher index = easier, lower index = harder
        
        if hole_par == 3:
            avg_score = 3.0 + np.round(np.random.uniform(0.3, 0.6) + 0.2 * difficulty_weight, 2)
            sg = np.round(-0.15 - 0.25 * difficulty_weight, 2)
            gir = int(np.round(45 - 20 * difficulty_weight))
            putts = np.round(1.75 + 0.15 * difficulty_weight, 2)
            birdie, par_pct, bogey, double = 8, 52, 35, 5
        elif hole_par == 5:
            avg_score = 5.0 + np.round(np.random.uniform(0.2, 0.5) + 0.3 * difficulty_weight, 2)
            sg = np.round(-0.10 - 0.30 * difficulty_weight, 2)
            gir = int(np.round(40 - 20 * difficulty_weight))
            putts = np.round(1.80 + 0.15 * difficulty_weight, 2)
            birdie, par_pct, bogey, double = 12, 48, 30, 10
        else:
            avg_score = 4.0 + np.round(np.random.uniform(0.35, 0.7) + 0.35 * difficulty_weight, 2)
            sg = np.round(-0.20 - 0.35 * difficulty_weight, 2)
            gir = int(np.round(30 - 20 * difficulty_weight))
            putts = np.round(1.80 + 0.15 * difficulty_weight, 2)
            birdie, par_pct, bogey, double = 5, 45, 40, 10
            
        # Standardize distribution summing to 100%
        tot = birdie + par_pct + bogey + double
        birdie = int(np.round(birdie * 100 / tot))
        par_pct = int(np.round(par_pct * 100 / tot))
        bogey = int(np.round(bogey * 100 / tot))
        double = 100 - (birdie + par_pct + bogey)
        
        tips = {
            3: f"Standard Par 3 on {course_name}. Pin position determines difficulty. Choose a club to clear the front boundary and center your shot.",
            4: f"Tight Par 4 requiring precision from the tee. Avoid fairway bunkers on the right and check wind speed before committing to your wedge.",
            5: f"Reachable Par 5. Play conservatively down the fairway to set up a clean third shot. Green features a subtle right-to-left break."
        }
        
        holes.append({
            "Hole": h,
            "Par": hole_par,
            "Yards": y,
            "Index": h_idx,
            "AvgScore": avg_score,
            "SG": sg,
            "GIR": max(5, gir),
            "Putts": putts,
            "Birdie": birdie,
            "ParPct": par_pct,
            "Bogey": bogey,
            "Double": double,
            "Tip": tips[hole_par]
        })
        
    return pd.DataFrame(holes)

# ============================================================================= =
# 4. DASH APP STRUCTURAL BOOTSTRAP
# ============================================================================= =
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div(
    style={
        'backgroundColor': '#121212',
        'color': '#f5f5f5',
        'fontFamily': '"Segoe UI", Roboto, Helvetica, Arial, sans-serif',
        'padding': '0px',
        'margin': '0px',
        'minHeight': '100vh'
    },
    children=[
        # Navigation Bar Header
        html.Div(
            style={
                'backgroundColor': '#1e1e1e',
                'padding': '15px 30px',
                'borderBottom': '3px solid #2ecc71',
                'display': 'flex',
                'justifyContent': 'space-between',
                'alignItems': 'center'
            },
            children=[
                html.H1("Back in Bounds: Golf Performance Analytics", style={'margin': '0', 'fontSize': '24px', 'fontWeight': '600', 'color': '#ffffff'}),
                html.Div(
                    style={'textAlign': 'right'},
                    children=[
                        html.Span("Colin P.", style={'fontWeight': 'bold', 'color': '#2ecc71', 'fontSize': '16px'}),
                        html.Span(" (10 HCP / Multi-Course Analytics)", style={'color': '#888888', 'marginLeft': '5px', 'fontSize': '14px'})
                    ]
                )
            ],
            id='main-header'
        ),
        
        # Navigation Tabs with Styled Material Look
        html.Div(
            style={'padding': '10px 30px 0px 30px', 'backgroundColor': '#1a1a1a'},
            children=[
                dcc.Tabs(
                    id="main-tabs",
                    value='tab-round',
                    style={'height': '50px'},
                    colors={
                        "border": "#2c2c2c",
                        "primary": "#2ecc71",
                        "background": "#1e1e1e"
                    },
                    children=[
                        dcc.Tab(
                            label='Round Analysis',
                            value='tab-round',
                            style={'backgroundColor': '#1a1a1a', 'color': '#aaaaaa', 'border': 'none', 'borderBottom': '3px solid transparent', 'fontWeight': 'bold', 'padding': '12px'},
                            selected_style={'backgroundColor': '#1a1a1a', 'color': '#2ecc71', 'border': 'none', 'borderBottom': '3px solid #2ecc71', 'fontWeight': 'bold', 'padding': '12px'},
                            id='tab-round-btn'
                        ),
                        dcc.Tab(
                            label='Range Sessions',
                            value='tab-practice',
                            style={'backgroundColor': '#1a1a1a', 'color': '#aaaaaa', 'border': 'none', 'borderBottom': '3px solid transparent', 'fontWeight': 'bold', 'padding': '12px'},
                            selected_style={'backgroundColor': '#1a1a1a', 'color': '#2ecc71', 'border': 'none', 'borderBottom': '3px solid #2ecc71', 'fontWeight': 'bold', 'padding': '12px'},
                            id='tab-practice-btn'
                        )
                    ]
                )
            ]
        ),
        
        # Main Tab Content Stage
        html.Div(id='tabs-content', style={'padding': '30px', 'maxWidth': '1400px', 'margin': '0 auto'})
    ]
)

# ============================================================================= =
# 5. TAB CONTENT CALLBACK
# ============================================================================= =
@app.callback(
    Output('tabs-content', 'children'),
    Input('main-tabs', 'value')
)
def render_content(tab):
    if tab == 'tab-practice':
        # PRACTICE TAB (Launch Monitor analysis)
        return html.Div([
            html.Div(
                style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '20px'},
                children=[
                    html.H2('Practice Analytics (Launch Monitor)', style={'margin': '0', 'fontWeight': '400', 'color': '#ffffff'}),
                    html.Span("Stand-alone Demo Dataset Loaded", style={'backgroundColor': '#2c2c2c', 'color': '#888888', 'padding': '5px 12px', 'borderRadius': '15px', 'fontSize': '12px'})
                ]
            ),
            
            # Interactive Global Scatter Plot Card
            html.Div(
                style={'backgroundColor': '#1e1e1e', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.3)', 'marginBottom': '30px'},
                children=[
                    dcc.Graph(id='global-gapping-scatter', figure=global_fig)
                ]
            ),
            
            # Deep Dive Header
            html.Div(
                style={'borderTop': '1px solid #2c2c2c', 'paddingTop': '30px', 'marginBottom': '20px'},
                children=[
                    html.H3("Single Club Deep Dive Analysis", style={'margin': '0 0 10px 0', 'color': '#ffffff'}),
                    html.P("Select a club from your bag to analyze speed vs. distance and monitor strike quality trends over time.", style={'margin': '0', 'color': '#aaaaaa', 'fontSize': '14px'})
                ]
            ),
            
            # Selector Row
            html.Div(
                style={'marginBottom': '20px', 'backgroundColor': '#1e1e1e', 'padding': '15px 20px', 'borderRadius': '8px', 'display': 'flex', 'alignItems': 'center', 'gap': '15px'},
                children=[
                    html.Label("Select Club:", style={'fontWeight': 'bold', 'fontSize': '14px', 'color': '#ffffff'}),
                    dcc.Dropdown(
                        id='club-selector',
                        options=[{'label': club, 'value': club} for club in sorted(df['Club'].unique())],
                        value=df['Club'].iloc[0] if not df.empty else None,
                        style={'width': '220px', 'color': '#121212', 'fontFamily': 'inherit'}
                    ),
                ]
            ),
            
            # Side-by-side Charts Container
            html.Div(
                style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '25px'},
                children=[
                    # Chart 1: Speed vs Distance
                    html.Div(
                        style={'flex': '1', 'minWidth': '450px', 'backgroundColor': '#1e1e1e', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.3)'},
                        children=[
                            dcc.Graph(id='dist-speed-scatter')
                        ]
                    ),
                    # Chart 2: Smash Factor Trend
                    html.Div(
                        style={'flex': '1', 'minWidth': '450px', 'backgroundColor': '#1e1e1e', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.3)'},
                        children=[
                            dcc.Graph(id='smash-factor-trend')
                        ]
                    )
                ]
            )
        ])
    
    elif tab == 'tab-round':
        # MULTI-COURSE ROUND ANALYSIS TAB
        return html.Div([
            html.H2('Round Analysis (Multi-Course Statistics)', style={'marginBottom': '10px', 'fontWeight': '400', 'color': '#ffffff'}),
            html.P("Analyze course performance, map strategies, and upload round telemetry. Select a course and hole on the left to see localized analytics on the right.", style={'color': '#aaaaaa', 'fontSize': '14px', 'marginBottom': '25px'}),
            
            # Split-Screen Layout (Side-by-Side)
            html.Div(
                style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '30px'},
                children=[
                    # COLUMN 1: LEFT SIDE (Controls, Metrics & Upload) - Flex: 1.1
                    html.Div(
                        style={'flex': '1.1', 'minWidth': '400px', 'display': 'flex', 'flexDirection': 'column', 'gap': '20px'},
                        children=[
                            # Course Selection Card
                            html.Div(
                                style={'backgroundColor': '#1e1e1e', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.3)'},
                                children=[
                                    html.H4("Course Selection", style={'margin': '0 0 15px 0', 'color': '#ffffff', 'fontWeight': '600', 'fontSize': '16px'}),
                                    html.Div(
                                        style={'display': 'flex', 'flexDirection': 'column', 'gap': '10px'},
                                        children=[
                                            html.Label("Select Golf Course:", style={'fontWeight': 'bold', 'fontSize': '14px', 'color': '#ffffff'}),
                                            dcc.Dropdown(
                                                id='course-selector',
                                                options=[{'label': c, 'value': c} for c in sorted(COURSES_DB.keys())],
                                                value="Fermoy Golf Club",
                                                style={'width': '100%', 'color': '#121212', 'fontFamily': 'inherit'}
                                            ),
                                            html.Div(
                                                style={'marginTop': '10px', 'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'},
                                                children=[
                                                    html.Span("Tracking Status:", style={'color': '#888', 'fontSize': '13px'}),
                                                    html.Span(id='course-status-badge', style={'padding': '4px 12px', 'borderRadius': '12px', 'fontSize': '12px', 'fontWeight': 'bold'})
                                                ]
                                            )
                                        ]
                                    )
                                ]
                            ),
                            
                            # Hole Selection Card
                            html.Div(
                                style={'backgroundColor': '#1e1e1e', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.3)'},
                                children=[
                                    html.H4("Hole Selector & Attributes", style={'margin': '0 0 15px 0', 'color': '#ffffff', 'fontWeight': '600', 'fontSize': '16px'}),
                                    html.Div(
                                        style={'display': 'flex', 'flexDirection': 'column', 'gap': '12px'},
                                        children=[
                                            html.Div(
                                                style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'},
                                                children=[
                                                    html.Label("Select Hole:", style={'fontWeight': 'bold', 'fontSize': '14px', 'color': '#ffffff'}),
                                                    html.Span(id='hole-attributes-tag', style={'backgroundColor': '#2c2c2c', 'color': '#2ecc71', 'padding': '4px 12px', 'borderRadius': '12px', 'fontSize': '12px', 'fontWeight': 'bold'})
                                                ]
                                            ),
                                            dcc.Dropdown(
                                                id='hole-selector',
                                                style={'width': '100%', 'color': '#121212', 'fontFamily': 'inherit'}
                                            ),
                                        ]
                                    )
                                ]
                            ),
                            
                            # Metrics Cards Grid
                            html.Div(
                                style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '15px'},
                                children=[
                                    # Card A: Avg Score
                                    html.Div(
                                        style={'backgroundColor': '#1e1e1e', 'padding': '15px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.3)', 'textAlign': 'center'},
                                        children=[
                                            html.H6("YOUR AVG SCORE", style={'margin': '0', 'color': '#aaaaaa', 'fontSize': '11px', 'letterSpacing': '1px'}),
                                            html.H3(id='deep-dive-avg-score', style={'margin': '8px 0 0 0', 'fontSize': '24px', 'color': '#ffffff'})
                                        ]
                                    ),
                                    # Card B: Strokes Gained
                                    html.Div(
                                        style={'backgroundColor': '#1e1e1e', 'padding': '15px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.3)', 'textAlign': 'center'},
                                        id='deep-dive-sg-card',
                                        children=[
                                            html.H6("SG VS. 5 HCP TARGET", style={'margin': '0', 'color': '#aaaaaa', 'fontSize': '11px', 'letterSpacing': '1px'}),
                                            html.H3(id='deep-dive-sg-val', style={'margin': '8px 0 0 0', 'fontSize': '24px', 'color': '#ff4d4d'})
                                        ]
                                    ),
                                    # Card C: GIR %
                                    html.Div(
                                        style={'backgroundColor': '#1e1e1e', 'padding': '15px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.3)', 'textAlign': 'center'},
                                        children=[
                                            html.H6("GREEN IN REGULATION", style={'margin': '0', 'color': '#aaaaaa', 'fontSize': '11px', 'letterSpacing': '1px'}),
                                            html.H3(id='deep-dive-gir', style={'margin': '8px 0 0 0', 'fontSize': '24px', 'color': '#3498db'})
                                        ]
                                    ),
                                    # Card D: Putts
                                    html.Div(
                                        style={'backgroundColor': '#1e1e1e', 'padding': '15px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.3)', 'textAlign': 'center'},
                                        children=[
                                            html.H6("AVG PUTTS PER HOLE", style={'margin': '0', 'color': '#aaaaaa', 'fontSize': '11px', 'letterSpacing': '1px'}),
                                            html.H3(id='deep-dive-putts', style={'margin': '8px 0 0 0', 'fontSize': '24px', 'color': '#2980b9'})
                                        ]
                                    ),
                                ]
                            ),
                            
                            # Caddie Strategy Card
                            html.Div(
                                style={'backgroundColor': '#1e1e1e', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.3)', 'borderLeft': '5px solid #2ecc71'},
                                children=[
                                    html.H4("⛳ Caddie Strategy & Insights", style={'margin': '0 0 10px 0', 'color': '#2ecc71', 'fontWeight': 'bold', 'fontSize': '15px'}),
                                    html.P(id='deep-dive-strategy-tip', style={'margin': '0', 'color': '#f5f5f5', 'fontSize': '13px', 'lineHeight': '1.5'})
                                ]
                            ),
                            
                            # Screenshot Upload Zone (SDET Manual Upload Showcase)
                            html.Div(
                                style={'backgroundColor': '#1e1e1e', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.3)'},
                                children=[
                                    html.H4("📸 Upload Round Screenshot", style={'margin': '0 0 5px 0', 'color': '#ffffff', 'fontWeight': '600', 'fontSize': '15px'}),
                                    html.P("Finished a round? Upload your Arccos round overview screenshot to log it manually and update the course databases.", style={'margin': '0 0 15px 0', 'color': '#aaaaaa', 'fontSize': '12px', 'lineHeight': '1.4'}),
                                    dcc.Upload(
                                        id='upload-round-screenshot',
                                        children=html.Div([
                                            'Drag and Drop or ',
                                            html.A('Browse File', style={'color': '#2ecc71', 'fontWeight': 'bold', 'textDecoration': 'underline'})
                                        ]),
                                        style={
                                            'width': '100%',
                                            'height': '65px',
                                            'lineHeight': '65px',
                                            'borderWidth': '2px',
                                            'borderStyle': 'dashed',
                                            'borderRadius': '6px',
                                            'textAlign': 'center',
                                            'borderColor': '#444',
                                            'backgroundColor': '#121212',
                                            'cursor': 'pointer',
                                            'fontSize': '13px',
                                            'color': '#aaa'
                                        },
                                        multiple=True
                                    ),
                                    html.Div(id='uploaded-screenshots-container')
                                ]
                            )
                        ]
                    ),
                    
                    # COLUMN 2: RIGHT SIDE (Course Summary Cards, Bar Chart, Donut Chart) - Flex: 1.8
                    html.Div(
                        style={'flex': '1.8', 'minWidth': '550px', 'display': 'flex', 'flexDirection': 'column', 'gap': '20px'},
                        children=[
                            # Limited Data Mode Banner Placeholder
                            html.Div(id='limited-data-banner-container'),
                            
                            # Course Summary Cards Grid (Inside right column)
                            html.Div(
                                style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(130px, 1fr))', 'gap': '15px'},
                                children=[
                                    html.Div(
                                        style={'backgroundColor': '#1e1e1e', 'padding': '15px', 'borderRadius': '8px', 'borderLeft': '4px solid #2ecc71', 'textAlign': 'center'},
                                        children=[
                                            html.H6("SCORECARD", style={'margin': '0', 'color': '#aaaaaa', 'fontSize': '11px', 'letterSpacing': '0.5px'}),
                                            html.H4(id='overview-par-yards', style={'margin': '6px 0 2px 0', 'fontSize': '16px', 'color': '#2ecc71', 'fontWeight': 'bold'}),
                                            html.P(id='overview-location', style={'margin': '0', 'fontSize': '10px', 'color': '#888888'})
                                        ]
                                    ),
                                    html.Div(
                                        style={'backgroundColor': '#1e1e1e', 'padding': '15px', 'borderRadius': '8px', 'borderLeft': '4px solid #2ecc71', 'textAlign': 'center'},
                                        children=[
                                            html.H6("BEST HOLES", style={'margin': '0', 'color': '#aaaaaa', 'fontSize': '11px', 'letterSpacing': '0.5px'}),
                                            html.H4(id='overview-best-holes', style={'margin': '6px 0 2px 0', 'fontSize': '16px', 'color': '#2ecc71', 'fontWeight': 'bold'}),
                                            html.P(id='overview-best-sg', style={'margin': '0', 'fontSize': '10px', 'color': '#888888'})
                                        ]
                                    ),
                                    html.Div(
                                        style={'backgroundColor': '#1e1e1e', 'padding': '15px', 'borderRadius': '8px', 'borderLeft': '4px solid #ff4d4d', 'textAlign': 'center'},
                                        children=[
                                            html.H6("BOTTLENECK", style={'margin': '0', 'color': '#aaaaaa', 'fontSize': '11px', 'letterSpacing': '0.5px'}),
                                            html.H4(id='overview-worst-hole', style={'margin': '6px 0 2px 0', 'fontSize': '16px', 'color': '#ff4d4d', 'fontWeight': 'bold'}),
                                            html.P(id='overview-worst-details', style={'margin': '0', 'fontSize': '10px', 'color': '#888888'})
                                        ]
                                    ),
                                    html.Div(
                                        style={'backgroundColor': '#1e1e1e', 'padding': '15px', 'borderRadius': '8px', 'borderLeft': '4px solid #ff4d4d', 'textAlign': 'center'},
                                        children=[
                                            html.H6("AVG SCORE", style={'margin': '0', 'color': '#aaaaaa', 'fontSize': '11px', 'letterSpacing': '0.5px'}),
                                            html.H4(id='overview-avg-score', style={'margin': '6px 0 2px 0', 'fontSize': '16px', 'color': '#ff4d4d', 'fontWeight': 'bold'}),
                                            html.P(id='overview-overall-sg', style={'margin': '0', 'fontSize': '10px', 'color': '#888888'})
                                        ]
                                    )
                                ]
                            ),
                            
                            # Course strokes gained bar chart
                            html.Div(
                                style={'backgroundColor': '#1e1e1e', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.3)'},
                                children=[
                                    dcc.Graph(id='course-sg-bar')
                                ]
                            ),
                            
                            # Scoring Distribution Pie Chart
                            html.Div(
                                style={'backgroundColor': '#1e1e1e', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.3)'},
                                children=[
                                    dcc.Graph(id='hole-scoring-dist-chart')
                                ]
                            )
                        ]
                    )
                ]
            )
        ])
    return html.Div([html.H3("Content Not Available")])


# ==============================================================================
# 6. CALLBACKS
# ==============================================================================

# Callback for Single-Club Deep Dive (Range Sessions tab)
@app.callback(
    [Output('dist-speed-scatter', 'figure'),
     Output('smash-factor-trend', 'figure')],
    [Input('club-selector', 'value')]
)
def update_dashboard(selected_club):
    filtered_df = df[df['Club'] == selected_club].copy()
    
    # Chart 1: Speed vs Total Distance Scatter Plot
    fig1 = px.scatter(
        filtered_df,
        x='Club Speed',
        y='Total',
        trendline="ols" if len(filtered_df) > 1 else None,
        title=f"{selected_club}: Club Speed vs. Total Distance",
        template="plotly_dark",
        labels={'Total': 'Total Distance (yds)', 'Club Speed': 'Club Speed (mph)'}
    )
    fig1.update_layout(
        plot_bgcolor='#1a1a1a',
        paper_bgcolor='#1e1e1e',
        margin=dict(l=40, r=40, t=50, b=40)
    )
    
    # Sort chronologically for trend lines
    trend_df = filtered_df.dropna(subset=['Smash']).sort_values('Date')
    
    # Chart 2: Smash Factor Trend Line over time
    fig2 = px.line(
        trend_df,
        x='Date',
        y='Smash',
        markers=True,
        title=f"{selected_club}: Smash Factor Chronological Trend",
        template="plotly_dark",
        labels={'Smash': 'Smash Factor', 'Date': 'Date'}
    )
    fig2.update_layout(
        plot_bgcolor='#1a1a1a',
        paper_bgcolor='#1e1e1e',
        margin=dict(l=40, r=40, t=50, b=40),
        yaxis=dict(range=[1.0, 1.55])
    )
    
    return fig1, fig2


# Callback for updating Course Specific scorecard overview & hole list
@app.callback(
    [Output('course-status-badge', 'children'),
     Output('course-status-badge', 'style'),
     Output('limited-data-banner-container', 'children'),
     Output('overview-par-yards', 'children'),
     Output('overview-location', 'children'),
     Output('overview-best-holes', 'children'),
     Output('overview-best-sg', 'children'),
     Output('overview-worst-hole', 'children'),
     Output('overview-worst-details', 'children'),
     Output('overview-avg-score', 'children'),
     Output('overview-overall-sg', 'children'),
     Output('course-sg-bar', 'figure'),
     Output('hole-selector', 'options'),
     Output('hole-selector', 'value')],
    [Input('course-selector', 'value')]
)
def update_course_selection(course_name):
    metadata = COURSES_DB.get(course_name, COURSES_DB["Fermoy Golf Club"])
    has_real = metadata["has_real_data"]
    
    # Status Badge styling
    badge_text = metadata["status"]
    if has_real:
        badge_style = {'backgroundColor': '#1b5e20', 'color': '#2ecc71', 'padding': '4px 12px', 'borderRadius': '12px', 'fontSize': '12px', 'fontWeight': 'bold'}
        banner_child = None
    else:
        badge_style = {'backgroundColor': '#4a2306', 'color': '#f39c12', 'padding': '4px 12px', 'borderRadius': '12px', 'fontSize': '12px', 'fontWeight': 'bold'}
        banner_child = html.Div(
            style={'backgroundColor': '#2c2514', 'border': '1px solid #d35400', 'color': '#f39c12', 'padding': '15px', 'borderRadius': '6px', 'marginBottom': '20px', 'fontSize': '13px'},
            children=[
                html.Strong("⚠️ Limited Data Mode: "),
                f"No Arccos round files have been uploaded for {course_name} yet. Displaying baseline estimated performance metrics for a 10 HCP golfer. Upload your on-course Arccos data to unlock personalized analytics."
            ]
        )
        
    # Overview metrics
    par_yards_str = f"Par {metadata['par']} / {metadata['yards']:,}y"
    loc_str = metadata["location"]
    best_holes = metadata["best_holes"]
    best_sg_str = "+0.05 SG vs. 5 HCP" if has_real else "Estimated Strengths"
    worst_hole = metadata["worst_hole"]
    worst_details = "-0.65 SG (442y Par 4)" if has_real else "Estimated Bottleneck"
    avg_score_str = f"{metadata['avg_score']:.1f} Avg"
    overall_sg_str = f"{metadata['overall_sg']:+.1f} SG vs. 5 HCP"
    
    # Load hole DataFrame for course
    holes_df = get_course_holes_df(course_name)
    
    # Generate overview bar chart
    sg_values = holes_df['SG'].tolist()
    colors = ['#ff4d4d' if val < 0 else '#2ecc71' for val in sg_values]
    labels = [f"Hole {h}" for h in holes_df['Hole']]
    
    sg_fig = go.Figure(go.Bar(
        x=labels,
        y=sg_values,
        marker_color=colors,
        text=[f"{val:+.2f}" for val in sg_values],
        textposition='outside',
        hovertemplate='Hole %{x}: %{y:+.2f} Strokes Gained vs 5 HCP<extra></extra>'
    ))
    sg_fig.update_layout(
        title=f"{course_name}: Strokes Gained/Lost per Hole (vs. 5 HCP Target)",
        template="plotly_dark",
        plot_bgcolor='#1a1a1a',
        paper_bgcolor='#1e1e1e',
        margin=dict(l=40, r=40, t=60, b=40),
        yaxis_title="Strokes Gained / Hole",
        yaxis=dict(gridcolor='#2c2c2c'),
        xaxis=dict(gridcolor='#2c2c2c')
    )
    
    # Hole dropdown options
    hole_options = [{'label': f"Hole {h} (Par {holes_df.loc[h-1, 'Par']})", 'value': h} for h in holes_df['Hole']]
    
    return (
        badge_text, badge_style, banner_child, 
        par_yards_str, loc_str, best_holes, best_sg_str,
        worst_hole, worst_details, avg_score_str, overall_sg_str,
        sg_fig, hole_options, 1
    )


# Callback for updating Specific Hole Deep Dive within Selected Course
@app.callback(
    [Output('hole-attributes-tag', 'children'),
     Output('deep-dive-avg-score', 'children'),
     Output('deep-dive-sg-val', 'children'),
     Output('deep-dive-sg-card', 'style'),
     Output('deep-dive-gir', 'children'),
     Output('deep-dive-putts', 'children'),
     Output('deep-dive-strategy-tip', 'children'),
     Output('hole-scoring-dist-chart', 'figure')],
    [Input('course-selector', 'value'),
     Input('hole-selector', 'value')]
)
def update_hole_analysis(course_name, selected_hole):
    # Safe defaults if callback fires out-of-order during course switch
    if selected_hole is None:
        selected_hole = 1
        
    holes_df = get_course_holes_df(course_name)
    row = holes_df[holes_df['Hole'] == selected_hole].iloc[0]
    
    # Header tag text
    attr_text = f"Yardage: {row['Yards']}y | Index: {row['Index']}"
    
    # Formatting scoring average and strokes gained
    avg_score_str = f"{row['AvgScore']:.2f} ({row['AvgScore'] - row['Par']:+.2f})"
    sg_str = f"{row['SG']:+.2f}"
    
    # Color-code Strokes Gained card border depending on positive/negative
    sg_card_color = '#2ecc71' if row['SG'] >= 0 else '#ff4d4d'
    sg_card_style = {
        'backgroundColor': '#1e1e1e', 
        'padding': '15px 20px', 
        'borderRadius': '8px', 
        'boxShadow': '0 4px 6px rgba(0,0,0,0.3)', 
        'textAlign': 'center', \
        'borderBottom': f'4px solid {sg_card_color}'
    }
    
    gir_str = f"{row['GIR']}%"
    putts_str = f"{row['Putts']:.2f}"
    tip_text = row['Tip']
    
    # Generate Hole Scoring Distribution Donut Chart
    labels = ['Birdie', 'Par', 'Bogey', 'Double+']
    values = [row['Birdie'], row['ParPct'], row['Bogey'], row['Double']]
    
    colors = ['#2ecc71', '#3498db', '#f1c40f', '#e74c3c']
    
    # Filter out 0% slices to avoid cluttered visuals
    filtered_labels = [l for l, v in zip(labels, values) if v > 0]
    filtered_values = [v for v in values if v > 0]
    filtered_colors = [c for c, v in zip(colors, values) if v > 0]
    
    dist_fig = go.Figure(data=[go.Pie(
        labels=filtered_labels,
        values=filtered_values,
        hole=.4,
        marker=dict(colors=filtered_colors),
        textinfo='percent+label',
        hovertemplate='%{label}: %{value}% of rounds<extra></extra>'
    )])
    dist_fig.update_layout(
        title=f"Hole {selected_hole} Scoring Profile ({course_name})",
        template="plotly_dark",
        plot_bgcolor='#1a1a1a',
        paper_bgcolor='#1e1e1e',
        margin=dict(l=30, r=30, t=50, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
    )
    
    return attr_text, avg_score_str, sg_str, sg_card_style, gir_str, putts_str, tip_text, dist_fig


# Callback for simulated screenshot upload parsing success
@app.callback(
    Output('uploaded-screenshots-container', 'children'),
    Input('upload-round-screenshot', 'contents'),
    prevent_initial_call=True
)
def display_upload_success(contents_list):
    if contents_list:
        return html.Div(
            style={
                'marginTop': '15px', 
                'backgroundColor': '#1b5e20', 
                'border': '1px solid #2ecc71',
                'color': '#2ecc71', 
                'padding': '12px 15px', 
                'borderRadius': '6px', 
                'fontSize': '12px', 
                'display': 'flex', 
                'alignItems': 'center', 
                'gap': '10px',
                'lineHeight': '1.4'
            },
            children=[
                html.Span("✓", style={'fontWeight': 'bold', 'fontSize': '16px'}),
                f"Uploaded {len(contents_list)} round screenshot(s) successfully! Telemetry parsed and logged to database."
            ]
        )
    return None


# ============================================================================= =
# 7. MAIN RUN STATEMENT
# ============================================================================= =
if __name__ == '__main__':
    app.run(debug=True)
