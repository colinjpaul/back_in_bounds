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

# ==============================================================================
# 3. FERMOY GOLF CLUB HOLE-BY-HOLE PERFORMANCE DATASET
# ==============================================================================

fermoy_holes_df = pd.DataFrame([
    {"Hole": 1, "Par": 4, "Yards": 361, "Index": 12, "AvgScore": 4.35, "SG": -0.15, "GIR": 35, "Putts": 1.8, "Birdie": 5, "Par": 55, "Bogey": 35, "Double": 5, "Tip": "A gentle opening Par 4. Favor the right side of the fairway as everything slopes left. A solid drive leaves a short iron into a flat green."},
    {"Hole": 2, "Par": 4, "Yards": 388, "Index": 10, "AvgScore": 4.50, "SG": -0.25, "GIR": 25, "Putts": 1.9, "Birdie": 5, "Par": 45, "Bogey": 40, "Double": 10, "Tip": "Blind tee shot. Aim at the white marker post. The approach shot plays slightly downhill, so take one less club if the wind is down."},
    {"Hole": 3, "Par": 4, "Yards": 437, "Index": 2, "AvgScore": 5.15, "SG": -0.60, "GIR": 10, "Putts": 2.0, "Birdie": 0, "Par": 20, "Bogey": 50, "Double": 30, "Tip": "A monster Par 4 playing uphill. GIR is extremely rare here. Strategy: Treat this as a three-shot hole. Lay up to your favorite wedge distance and rely on your strong short game (+0.8 SG) to scramble for par."},
    {"Hole": 4, "Par": 3, "Yards": 143, "Index": 18, "AvgScore": 3.15, "SG": 0.05, "GIR": 55, "Putts": 1.7, "Birdie": 15, "Par": 65, "Bogey": 15, "Double": 5, "Tip": "Your best performing hole! A short Par 3 with a large green. Club selection is key; trust your PW (125 yds) or 9i if playing into a breeze. Avoid going long at all costs."},
    {"Hole": 5, "Par": 4, "Yards": 396, "Index": 8, "AvgScore": 4.65, "SG": -0.35, "GIR": 20, "Putts": 1.8, "Birdie": 5, "Par": 40, "Bogey": 45, "Double": 10, "Tip": "Overshooting the green here leaves a very tricky chip. Play to the front of the green and let your putter do the work."},
    {"Hole": 6, "Par": 4, "Yards": 350, "Index": 14, "AvgScore": 4.40, "SG": -0.20, "GIR": 40, "Putts": 1.8, "Birdie": 10, "Par": 50, "Bogey": 30, "Double": 10, "Tip": "A shorter Par 4, but tight off the tee. Ditch the driver and hit a 5-wood or 4-iron to guarantee finding the fairway and giving yourself a clean wedge look."},
    {"Hole": 7, "Par": 5, "Yards": 513, "Index": 4, "AvgScore": 5.25, "SG": -0.15, "GIR": 30, "Putts": 1.9, "Birdie": 15, "Par": 50, "Bogey": 25, "Double": 10, "Tip": "Double dogleg Par 5. The second shot must be positioned on the right side of the fairway to have any view of the green for your third."},
    {"Hole": 8, "Par": 3, "Yards": 168, "Index": 16, "AvgScore": 3.45, "SG": -0.20, "GIR": 40, "Putts": 1.8, "Birdie": 5, "Par": 55, "Bogey": 35, "Double": 5, "Tip": "A tricky Par 3 playing to an elevated green. Take one extra club (7-iron instead of 8-iron) to clear the front bunkers."},
    {"Hole": 9, "Par": 4, "Yards": 411, "Index": 6, "AvgScore": 4.75, "SG": -0.40, "GIR": 15, "Putts": 1.9, "Birdie": 0, "Par": 35, "Bogey": 55, "Double": 10, "Tip": "Tough finishing hole on the front nine. Aim your drive down the left-center. The green has a severe slope from back to front—stay below the hole."},
    {"Hole": 10, "Par": 4, "Yards": 355, "Index": 15, "AvgScore": 4.35, "SG": -0.15, "GIR": 35, "Putts": 1.8, "Birdie": 10, "Par": 50, "Bogey": 35, "Double": 5, "Tip": "An excellent scoring opportunity. A good drive leaves a short wedge. Guard against getting lazy with your wedge distance control."},
    {"Hole": 11, "Par": 4, "Yards": 390, "Index": 9, "AvgScore": 4.60, "SG": -0.30, "GIR": 20, "Putts": 1.8, "Birdie": 5, "Par": 45, "Bogey": 40, "Double": 10, "Tip": "Aim for the right side of the fairway to open up the green. The green is narrow and heavily guarded by trees on the left."},
    {"Hole": 12, "Par": 3, "Yards": 198, "Index": 7, "AvgScore": 3.85, "SG": -0.45, "GIR": 15, "Putts": 1.9, "Birdie": 0, "Par": 35, "Bogey": 50, "Double": 15, "Tip": "A long, daunting Par 3. Your 5-iron or 5-wood is the play here. If you miss, miss short-right to leave an easy chip."},
    {"Hole": 13, "Par": 4, "Yards": 382, "Index": 11, "AvgScore": 4.55, "SG": -0.25, "GIR": 25, "Putts": 1.8, "Birdie": 5, "Par": 45, "Bogey": 45, "Double": 5, "Tip": "Slight dogleg right. A drive over the corner of the trees cuts off significant yardage, but safety lies down the left center."},
    {"Hole": 14, "Par": 4, "Yards": 404, "Index": 3, "AvgScore": 4.90, "SG": -0.50, "GIR": 15, "Putts": 1.9, "Birdie": 0, "Par": 30, "Bogey": 55, "Double": 15, "Tip": "Strong Par 4. The approach shot is uphill to a multi-tiered green. Take an extra club to ensure you reach the correct tier."},
    {"Hole": 15, "Par": 4, "Yards": 442, "Index": 1, "AvgScore": 5.25, "SG": -0.65, "GIR": 5, "Putts": 2.0, "Birdie": 0, "Par": 15, "Bogey": 50, "Double": 35, "Tip": "The Index 1 hole and your largest leakage on the course. At 442 yards, it's a par 5 for most. Strategy: Lay up off the tee or on your second shot to 60 yards. Play for a 5 and avoid the card-wrecking double bogeys."},
    {"Hole": 16, "Par": 5, "Yards": 532, "Index": 13, "AvgScore": 5.10, "SG": 0.05, "GIR": 45, "Putts": 1.8, "Birdie": 20, "Par": 55, "Bogey": 20, "Double": 5, "Tip": "Your second best performing hole! An authentic par 5 where your distance off the tee pays dividends. A good drive gives you a real chance to reach or get close in two."},
    {"Hole": 17, "Par": 3, "Yards": 151, "Index": 17, "AvgScore": 3.35, "SG": -0.15, "GIR": 45, "Putts": 1.8, "Birdie": 10, "Par": 55, "Bogey": 30, "Double": 5, "Tip": "A scenic Par 3 over a valley. Wind can be deceptive here. Throw some grass in the air to check the breeze and trust your 8 or 9-iron yardage."},
    {"Hole": 18, "Par": 4, "Yards": 382, "Index": 5, "AvgScore": 4.80, "SG": -0.45, "GIR": 20, "Putts": 1.9, "Birdie": 5, "Par": 35, "Bogey": 45, "Double": 15, "Tip": "Tough finishing hole playing back towards the clubhouse. Aim your tee shot left of the fairway bunker. The green is well-protected by deep greenside bunkers."}
])

# Pre-generate course strokes gained overview bar chart
fermoy_sg_values = fermoy_holes_df['SG'].tolist()
fermoy_colors = ['#ff4d4d' if val < 0 else '#2ecc71' for val in fermoy_sg_values]
fermoy_labels = [f"Hole {h}" for h in fermoy_holes_df['Hole']]

fermoy_sg_fig = go.Figure(go.Bar(
    x=fermoy_labels,
    y=fermoy_sg_values,
    marker_color=fermoy_colors,
    text=[f"{val:+.2f}" for val in fermoy_sg_values],
    textposition='outside',
    hovertemplate='Hole %{x}: %{y:+.2f} Strokes Gained vs 5 HCP<extra></extra>'
))
fermoy_sg_fig.update_layout(
    title="Fermoy Golf Club: Strokes Gained/Lost per Hole (vs. 5 HCP Target)",
    template="plotly_dark",
    plot_bgcolor='#1a1a1a',
    paper_bgcolor='#1e1e1e',
    margin=dict(l=40, r=40, t=60, b=40),
    yaxis_title="Strokes Gained / Hole",
    yaxis=dict(gridcolor='#2c2c2c'),
    xaxis=dict(gridcolor='#2c2c2c')
)

# ==============================================================================
# 4. DASH APP STRUCTURAL BOOTSTRAP
# ==============================================================================
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
                        html.Span(" (10 HCP / Fermoy Golf Club)", style={'color': '#888888', 'marginLeft': '5px', 'fontSize': '14px'})
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
                    value='tab-practice',
                    style={'height': '50px'},
                    colors={
                        "border": "#2c2c2c",
                        "primary": "#2ecc71",
                        "background": "#1e1e1e"
                    },
                    children=[
                        dcc.Tab(
                            label='Range Sessions',
                            value='tab-practice',
                            style={'backgroundColor': '#1a1a1a', 'color': '#aaaaaa', 'border': 'none', 'borderBottom': '3px solid transparent', 'fontWeight': 'bold', 'padding': '12px'},
                            selected_style={'backgroundColor': '#1a1a1a', 'color': '#2ecc71', 'border': 'none', 'borderBottom': '3px solid #2ecc71', 'fontWeight': 'bold', 'padding': '12px'},
                            id='tab-practice-btn'
                        ),
                        dcc.Tab(
                            label='Fermoy Hole Analysis',
                            value='tab-fermoy',
                            style={'backgroundColor': '#1a1a1a', 'color': '#aaaaaa', 'border': 'none', 'borderBottom': '3px solid transparent', 'fontWeight': 'bold', 'padding': '12px'},
                            selected_style={'backgroundColor': '#1a1a1a', 'color': '#2ecc71', 'border': 'none', 'borderBottom': '3px solid #2ecc71', 'fontWeight': 'bold', 'padding': '12px'},
                            id='tab-fermoy-btn'
                        ),
                    ]
                )
            ]
        ),
        
        # Main Tab Content Stage
        html.Div(id='tabs-content', style={'padding': '30px', 'maxWidth': '1400px', 'margin': '0 auto'})
    ]
)

# ==============================================================================
# 5. TAB CONTENT CALLBACK
# ==============================================================================
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
    
    elif tab == 'tab-fermoy':
        # FERMOY HOLE ANALYSIS TAB
        return html.Div([
            html.H2('Fermoy Golf Club Hole-by-Hole Analysis', style={'marginBottom': '25px', 'fontWeight': '400', 'color': '#ffffff'}),
            
            # Summary Metrics Row
            html.Div(
                style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '20px', 'marginBottom': '30px'},
                children=[
                    html.Div(
                        style={'flex': '1', 'minWidth': '220px', 'backgroundColor': '#1e1e1e', 'padding': '20px', 'borderRadius': '8px', 'borderLeft': '5px solid #2ecc71', 'textAlign': 'center'},
                        children=[
                            html.H5("FERMOY COURSE INFO", style={'margin': '0', 'color': '#aaaaaa', 'fontSize': '12px', 'letterSpacing': '1px'}),
                            html.H3("Par 71 / 6,403y", style={'margin': '10px 0 5px 0', 'fontSize': '26px', 'color': '#2ecc71'}),
                            html.P("Blue / White Championship Tees", style={'margin': '0', 'fontSize': '12px', 'color': '#888888'})
                        ]
                    ),
                    html.Div(
                        style={'flex': '1', 'minWidth': '220px', 'backgroundColor': '#1e1e1e', 'padding': '20px', 'borderRadius': '8px', 'borderLeft': '5px solid #2ecc71', 'textAlign': 'center'},
                        children=[
                            html.H5("BEST PERFORMING HOLES", style={'margin': '0', 'color': '#aaaaaa', 'fontSize': '12px', 'letterSpacing': '1px'}),
                            html.H3("Hole 4 & 16", style={'margin': '10px 0 5px 0', 'fontSize': '26px', 'color': '#2ecc71'}),
                            html.P("+0.05 SG vs. 5 HCP Target", style={'margin': '0', 'fontSize': '12px', 'color': '#888888'})
                        ]
                    ),
                    html.Div(
                        style={'flex': '1', 'minWidth': '220px', 'backgroundColor': '#1e1e1e', 'padding': '20px', 'borderRadius': '8px', 'borderLeft': '5px solid #ff4d4d', 'textAlign': 'center'},
                        children=[
                            html.H5("BIGGEST BOTTLENECK", style={'margin': '0', 'color': '#aaaaaa', 'fontSize': '12px', 'letterSpacing': '1px'}),
                            html.H3("Hole 15 (Index 1)", style={'margin': '10px 0 5px 0', 'fontSize': '26px', 'color': '#ff4d4d'}),
                            html.P("-0.65 SG (442y long Par 4)", style={'margin': '0', 'fontSize': '12px', 'color': '#888888'})
                        ]
                    ),
                    html.Div(
                        style={'flex': '1', 'minWidth': '220px', 'backgroundColor': '#1e1e1e', 'padding': '20px', 'borderRadius': '8px', 'borderLeft': '5px solid #ff4d4d', 'textAlign': 'center'},
                        children=[
                            html.H5("FERMOY AVG SCORE", style={'margin': '0', 'color': '#aaaaaa', 'fontSize': '12px', 'letterSpacing': '1px'}),
                            html.H3("81.3 Avg", style={'margin': '10px 0 5px 0', 'fontSize': '26px', 'color': '#ff4d4d'}),
                            html.P("-5.0 SG / Round vs. 5 HCP", style={'margin': '0', 'fontSize': '12px', 'color': '#888888'})
                        ]
                    )
                ]
            ),
            
            # Course-Wide Strokes Gained Bar Chart
            html.Div(
                style={'backgroundColor': '#1e1e1e', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.3)', 'marginBottom': '30px'},
                children=[
                    dcc.Graph(id='fermoy-sg-bar', figure=fermoy_sg_fig)
                ]
            ),
            
            # Interactive Deep Dive Section Header
            html.Div(
                style={'borderTop': '1px solid #2c2c2c', 'paddingTop': '30px', 'marginBottom': '20px'},
                children=[
                    html.H3("Hole-by-Hole Interactive Deep Dive", style={'margin': '0 0 10px 0', 'color': '#ffffff'}),
                    html.P("Select a hole from the 18 holes at Fermoy Golf Club to view your scoring metrics, GIR%, putting trends, and personalized strategy tips.", style={'margin': '0', 'color': '#aaaaaa', 'fontSize': '14px'})
                ]
            ),
            
            # Hole Selector Row
            html.Div(
                style={'marginBottom': '20px', 'backgroundColor': '#1e1e1e', 'padding': '15px 20px', 'borderRadius': '8px', 'display': 'flex', 'alignItems': 'center', 'gap': '15px'},
                children=[
                    html.Label("Select Hole:", style={'fontWeight': 'bold', 'fontSize': '14px', 'color': '#ffffff'}),
                    dcc.Dropdown(
                        id='hole-selector',
                        options=[{'label': f"Hole {h} (Par {fermoy_holes_df.loc[h-1, 'Par']})", 'value': h} for h in fermoy_holes_df['Hole']],
                        value=1,
                        style={'width': '220px', 'color': '#121212', 'fontFamily': 'inherit'}
                    ),
                    html.Span(id='hole-attributes-tag', style={'backgroundColor': '#2c2c2c', 'color': '#2ecc71', 'padding': '5px 12px', 'borderRadius': '15px', 'fontSize': '14px', 'fontWeight': 'bold'})
                ]
            ),
            
            # Deep Dive Content Area (Side-by-side or stacked layout)
            html.Div(
                style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '25px'},
                children=[
                    # Left side: Metrics & Strategy Card
                    html.Div(
                        style={'flex': '1', 'minWidth': '450px', 'display': 'flex', 'flexDirection': 'column', 'gap': '20px'},
                        children=[
                            # Metric Cards Grid
                            html.Div(
                                style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '15px'},
                                children=[
                                    # Card A: Avg Score
                                    html.Div(
                                        style={'backgroundColor': '#1e1e1e', 'padding': '15px 20px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.3)', 'textAlign': 'center'},
                                        children=[
                                            html.H6("YOUR AVG SCORE", style={'margin': '0', 'color': '#aaaaaa', 'fontSize': '11px', 'letterSpacing': '1px'}),
                                            html.H3(id='deep-dive-avg-score', style={'margin': '8px 0 0 0', 'fontSize': '28px', 'color': '#ffffff'})
                                        ]
                                    ),
                                    # Card B: Strokes Gained
                                    html.Div(
                                        style={'backgroundColor': '#1e1e1e', 'padding': '15px 20px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.3)', 'textAlign': 'center', 'borderBottom': '3px solid #ff4d4d'},
                                        id='deep-dive-sg-card',
                                        children=[
                                            html.H6("SG VS. 5 HCP TARGET", style={'margin': '0', 'color': '#aaaaaa', 'fontSize': '11px', 'letterSpacing': '1px'}),
                                            html.H3(id='deep-dive-sg-val', style={'margin': '8px 0 0 0', 'fontSize': '28px', 'color': '#ff4d4d'})
                                        ]
                                    ),
                                    # Card C: GIR %
                                    html.Div(
                                        style={'backgroundColor': '#1e1e1e', 'padding': '15px 20px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.3)', 'textAlign': 'center'},
                                        children=[
                                            html.H6("GREEN IN REGULATION (GIR)", style={'margin': '0', 'color': '#aaaaaa', 'fontSize': '11px', 'letterSpacing': '1px'}),
                                            html.H3(id='deep-dive-gir', style={'margin': '8px 0 0 0', 'fontSize': '28px', 'color': '#3498db'})
                                        ]
                                    ),
                                    # Card D: Putts
                                    html.Div(
                                        style={'backgroundColor': '#1e1e1e', 'padding': '15px 20px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.3)', 'textAlign': 'center'},
                                        children=[
                                            html.H6("AVG PUTTS PER HOLE", style={'margin': '0', 'color': '#aaaaaa', 'fontSize': '11px', 'letterSpacing': '1px'}),
                                            html.H3(id='deep-dive-putts', style={'margin': '8px 0 0 0', 'fontSize': '28px', 'color': '#2980b9'})
                                        ]
                                    ),
                                ]
                            ),
                            
                            # Caddie Strategy Card
                            html.Div(
                                style={'backgroundColor': '#1e1e1e', 'padding': '25px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.3)', 'borderLeft': '5px solid #2ecc71', 'flexGrow': '1'},
                                children=[
                                    html.H4("⛳ Caddie Strategy & Insights", style={'margin': '0 0 12px 0', 'color': '#2ecc71', 'fontWeight': 'bold'}),
                                    html.P(id='deep-dive-strategy-tip', style={'margin': '0', 'color': '#f5f5f5', 'fontSize': '14px', 'lineHeight': '1.6'})
                                ]
                            )
                        ]
                    ),
                    
                    # Right side: Scoring Distribution Chart
                    html.Div(
                        style={'flex': '1', 'minWidth': '450px', 'backgroundColor': '#1e1e1e', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.3)'},
                        children=[
                            dcc.Graph(id='hole-scoring-dist-chart')
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


# Callback for Fermoy Hole Analysis Deep Dive
@app.callback(
    [Output('hole-attributes-tag', 'children'),
     Output('deep-dive-avg-score', 'children'),
     Output('deep-dive-sg-val', 'children'),
     Output('deep-dive-sg-card', 'style'),
     Output('deep-dive-gir', 'children'),
     Output('deep-dive-putts', 'children'),
     Output('deep-dive-strategy-tip', 'children'),
     Output('hole-scoring-dist-chart', 'figure')],
    [Input('hole-selector', 'value')]
)
def update_hole_analysis(selected_hole):
    row = fermoy_holes_df[fermoy_holes_df['Hole'] == selected_hole].iloc[0]
    
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
        'textAlign': 'center', 
        'borderBottom': f'4px solid {sg_card_color}'
    }
    
    gir_str = f"{row['GIR']}%"
    putts_str = f"{row['Putts']:.2f}"
    tip_text = row['Tip']
    
    # Generate Hole Scoring Distribution Donut Chart
    labels = ['Birdie', 'Par', 'Bogey', 'Double+']
    values = [row['Birdie'], row['Par'], row['Bogey'], row['Double']]
    
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
        title=f"Hole {selected_hole} Scoring Distribution Profile",
        template="plotly_dark",
        plot_bgcolor='#1a1a1a',
        paper_bgcolor='#1e1e1e',
        margin=dict(l=30, r=30, t=50, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
    )
    
    return attr_text, avg_score_str, sg_str, sg_card_style, gir_str, putts_str, tip_text, dist_fig


# ==============================================================================
# 7. MAIN RUN STATEMENT
# ==============================================================================
if __name__ == '__main__':
    app.run(debug=True)
