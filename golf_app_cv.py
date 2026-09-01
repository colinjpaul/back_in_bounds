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
# 3. PRE-DEFINED ARCCOS COURSE PERFORMANCE DATA
# ==============================================================================
# Colin P. / 10 HCP / 8734 Shots / 114 Rounds
arccos_summary = {
    'handicap': '10.0',
    'shots': '8,734',
    'rounds': '114',
    'overall_sg': -6.0,
    'driving_sg': -1.1,
    'approach_sg': -3.9,
    'short_sg': 0.8,
    'putting_sg': -1.9
}

arccos_insights = [
    {"rank": 1, "game": "Putting Game", "sg": -2.0, "details": "0-10 ft putts", "color": "#ff4d4d"},
    {"rank": 2, "game": "Approach Game", "sg": -1.5, "details": "100-150 yard approach shots", "color": "#ff4d4d"},
    {"rank": 3, "game": "Approach Game", "sg": -1.4, "details": "Shots from the rough", "color": "#ff4d4d"}
]

arccos_smart_distances = {
    'Dr': 246, '5w': 208, '5i': 189, '6i': 178, '7i': 164, '8i': 155, '9i': 140, 'Pw': 125, '50': 110, 'Aw': 115, '54': 95, '58': 78, 'X': 192
}

scoring_averages = {
    'Par 3s': {'avg': 3.7, 'sg': -0.3},
    'Par 4s': {'avg': 4.8, 'sg': -0.3},
    'Par 5s': {'avg': 5.7, 'sg': -0.5}
}

scoring_breakdown = {
    'Metric': ['Birdies', 'Pars', 'Bogeys', 'Double+'],
    'Colin': [0.7, 6.7, 7.7, 3.0],
    'Target (5 HCP)': [1.2, 8.9, 6.4, 1.6]
}

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
                        html.Span(" (10 HCP / 114 Rounds)", style={'color': '#888888', 'marginLeft': '5px', 'fontSize': '14px'})
                    ]
                )
            ]
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
                            selected_style={'backgroundColor': '#1a1a1a', 'color': '#2ecc71', 'border': 'none', 'borderBottom': '3px solid #2ecc71', 'fontWeight': 'bold', 'padding': '12px'}
                        ),
                        dcc.Tab(
                            label='Course Performance',
                            value='tab-arccos',
                            style={'backgroundColor': '#1a1a1a', 'color': '#aaaaaa', 'border': 'none', 'borderBottom': '3px solid transparent', 'fontWeight': 'bold', 'padding': '12px'},
                            selected_style={'backgroundColor': '#1a1a1a', 'color': '#2ecc71', 'border': 'none', 'borderBottom': '3px solid #2ecc71', 'fontWeight': 'bold', 'padding': '12px'}
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
    
    elif tab == 'tab-arccos':
        # COURSE PERFORMANCE TAB (Arccos overall analytics)
        
        # Pre-generate course performance graphics using defined datasets
        # A. Strokes Gained Breakdown (Bar Chart)
        categories = ['Driving', 'Approach', 'Short Game', 'Putting']
        sg_values = [arccos_summary['driving_sg'], arccos_summary['approach_sg'], arccos_summary['short_sg'], arccos_summary['putting_sg']]
        colors = ['#ff4d4d' if val < 0 else '#2ecc71' for val in sg_values]
        
        sg_fig = go.Figure(go.Bar(
            x=categories,
            y=sg_values,
            marker_color=colors,
            text=[f"{val:+.1f} SG" for val in sg_values],
            textposition='auto',
            hovertemplate='%{x}: %{y:+.1f} SG<extra></extra>'
        ))
        sg_fig.update_layout(
            title="Strokes Gained Breakdown per Round (vs 5 HCP)",
            template="plotly_dark",
            plot_bgcolor='#1a1a1a',
            paper_bgcolor='#1e1e1e',
            margin=dict(l=40, r=40, t=50, b=40),
            yaxis_title="Strokes Gained / Round",
            yaxis=dict(gridcolor='#2c2c2c')
        )
        
        # B. Smart Distances (Horizontal Bar Chart)
        clubs_list = list(arccos_smart_distances.keys())
        distances_list = list(arccos_smart_distances.values())
        
        # Sort from longest to shortest
        sorted_pairs = sorted(zip(distances_list, clubs_list), reverse=False) # False for visual bottom-to-top ascending
        dist_sorted, clubs_sorted = zip(*sorted_pairs)
        
        dist_fig = go.Figure(go.Bar(
            x=dist_sorted,
            y=clubs_sorted,
            orientation='h',
            marker=dict(
                color='#2ecc71',
                line=dict(color='#27ae60', width=1.5)
            ),
            text=dist_sorted,
            textposition='outside',
            hovertemplate='%{y}: %{x} yds<extra></extra>'
        ))
        dist_fig.update_layout(
            title="Arccos Smart Distances (Yards)",
            template="plotly_dark",
            plot_bgcolor='#1a1a1a',
            paper_bgcolor='#1e1e1e',
            margin=dict(l=50, r=50, t=50, b=40),
            xaxis_title="Smart Distance (Yards)",
            xaxis=dict(gridcolor='#2c2c2c', range=[0, 280])
        )
        
        # C. Scoring Breakdown comparison
        score_df = pd.DataFrame(scoring_breakdown)
        scoring_fig = go.Figure()
        scoring_fig.add_trace(go.Bar(
            name='Colin P. (10 HCP)',
            x=score_df['Metric'],
            y=score_df['Colin'],
            marker_color='#e74c3c'
        ))
        scoring_fig.add_trace(go.Bar(
            name='Target (5 HCP)',
            x=score_df['Metric'],
            y=score_df['Target (5 HCP)'],
            marker_color='#3498db'
        ))
        scoring_fig.update_layout(
            title="Scoring Breakdown vs. 5 HCP Target",
            barmode='group',
            template="plotly_dark",
            plot_bgcolor='#1a1a1a',
            paper_bgcolor='#1e1e1e',
            margin=dict(l=40, r=40, t=50, b=40),
            yaxis_title="Average Counts per Round",
            yaxis=dict(gridcolor='#2c2c2c')
        )

        return html.Div([
            html.H2('Course Performance Analytics (Arccos)', style={'marginBottom': '20px', 'fontWeight': '400', 'color': '#ffffff'}),
            
            # Row 1: Key Metric Highlights Cards
            html.Div(
                style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '20px', 'marginBottom': '30px'},
                children=[
                    # Card 1: Overall SG
                    html.Div(
                        style={'flex': '1', 'minWidth': '220px', 'backgroundColor': '#1e1e1e', 'padding': '20px', 'borderRadius': '8px', 'borderLeft': '5px solid #ff4d4d', 'textAlign': 'center'},
                        children=[
                            html.H5("OVERALL GAME", style={'margin': '0', 'color': '#aaaaaa', 'fontSize': '12px', 'letterSpacing': '1px'}),
                            html.H3("-6.0 SG", style={'margin': '10px 0 5px 0', 'fontSize': '32px', 'color': '#ff4d4d'}),
                            html.P("Strokes lost/round vs 5 HCP", style={'margin': '0', 'fontSize': '12px', 'color': '#888888'})
                        ]
                    ),
                    # Card 2: Short Game
                    html.Div(
                        style={'flex': '1', 'minWidth': '220px', 'backgroundColor': '#1e1e1e', 'padding': '20px', 'borderRadius': '8px', 'borderLeft': '5px solid #2ecc71', 'textAlign': 'center'},
                        children=[
                            html.H5("SHORT GAME (Strength)", style={'margin': '0', 'color': '#aaaaaa', 'fontSize': '12px', 'letterSpacing': '1px'}),
                            html.H3("+0.8 SG", style={'margin': '10px 0 5px 0', 'fontSize': '32px', 'color': '#2ecc71'}),
                            html.P("Strokes gained around greens", style={'margin': '0', 'fontSize': '12px', 'color': '#888888'})
                        ]
                    ),
                    # Card 3: Approach Game
                    html.Div(
                        style={'flex': '1', 'minWidth': '220px', 'backgroundColor': '#1e1e1e', 'padding': '20px', 'borderRadius': '8px', 'borderLeft': '5px solid #ff4d4d', 'textAlign': 'center'},
                        children=[
                            html.H5("APPROACH GAME", style={'margin': '0', 'color': '#aaaaaa', 'fontSize': '12px', 'letterSpacing': '1px'}),
                            html.H3("-3.9 SG", style={'margin': '10px 0 5px 0', 'fontSize': '32px', 'color': '#ff4d4d'}),
                            html.P("Largest handicap bottleneck", style={'margin': '0', 'fontSize': '12px', 'color': '#888888'})
                        ]
                    ),
                    # Card 4: Putting
                    html.Div(
                        style={'flex': '1', 'minWidth': '220px', 'backgroundColor': '#1e1e1e', 'padding': '20px', 'borderRadius': '8px', 'borderLeft': '5px solid #ff4d4d', 'textAlign': 'center'},
                        children=[
                            html.H5("PUTTING GAME", style={'margin': '0', 'color': '#aaaaaa', 'fontSize': '12px', 'letterSpacing': '1px'}),
                            html.H3("-1.9 SG", style={'margin': '10px 0 5px 0', 'fontSize': '32px', 'color': '#ff4d4d'}),
                            html.P("Strokes lost on green", style={'margin': '0', 'fontSize': '12px', 'color': '#888888'})
                        ]
                    ),
                ]
            ),
            
            # Row 2: Strokes Gained Chart & Top 3 Insights
            html.Div(
                style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '25px', 'marginBottom': '30px'},
                children=[
                    # Strokes Gained Chart Card
                    html.Div(
                        style={'flex': '1.3', 'minWidth': '500px', 'backgroundColor': '#1e1e1e', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.3)'},
                        children=[
                            dcc.Graph(id='sg-breakdown-bar', figure=sg_fig)
                        ]
                    ),
                    # Insights Card
                    html.Div(
                        style={'flex': '1', 'minWidth': '400px', 'backgroundColor': '#1e1e1e', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.3)', 'display': 'flex', 'flexDirection': 'column'},
                        children=[
                            html.H4("Top 3 Targets For Improvement", style={'margin': '0 0 15px 0', 'color': '#ffffff', 'fontWeight': '600'}),
                            html.Div(
                                style={'display': 'flex', 'flexDirection': 'column', 'gap': '15px', 'flexGrow': '1'},
                                children=[
                                    html.Div(
                                        style={'display': 'flex', 'alignItems': 'center', 'backgroundColor': '#1a1a1a', 'padding': '12px 15px', 'borderRadius': '6px', 'borderLeft': '4px solid #ff4d4d'},
                                        children=[
                                            html.Div("1", style={'backgroundColor': '#ff4d4d', 'color': '#121212', 'borderRadius': '50%', 'width': '24px', 'height': '24px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'fontWeight': 'bold', 'marginRight': '12px'}),
                                            html.Div(style={'flex': '1'}, children=[
                                                html.H5("Putting Game: 0-10 ft putts", style={'margin': '0 0 3px 0', 'color': '#ffffff', 'fontSize': '14px'}),
                                                html.P("Critical short putt conversion deficit.", style={'margin': '0', 'color': '#888888', 'fontSize': '12px'})
                                            ]),
                                            html.Div("-2.0 SG", style={'color': '#ff4d4d', 'fontWeight': 'bold', 'fontSize': '15px'})
                                        ]
                                    ),
                                    html.Div(
                                        style={'display': 'flex', 'alignItems': 'center', 'backgroundColor': '#1a1a1a', 'padding': '12px 15px', 'borderRadius': '6px', 'borderLeft': '4px solid #ff4d4d'},
                                        children=[
                                            html.Div("2", style={'backgroundColor': '#ff4d4d', 'color': '#121212', 'borderRadius': '50%', 'width': '24px', 'height': '24px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'fontWeight': 'bold', 'marginRight': '12px'}),
                                            html.Div(style={'flex': '1'}, children=[
                                                html.H5("Approach: 100-150 yd approach shots", style={'margin': '0 0 3px 0', 'color': '#ffffff', 'fontSize': '14px'}),
                                                html.P("Inconsistent wedge and short iron proximity.", style={'margin': '0', 'color': '#888888', 'fontSize': '12px'})
                                            ]),
                                            html.Div("-1.5 SG", style={'color': '#ff4d4d', 'fontWeight': 'bold', 'fontSize': '15px'})
                                        ]
                                    ),
                                    html.Div(
                                        style={'display': 'flex', 'alignItems': 'center', 'backgroundColor': '#1a1a1a', 'padding': '12px 15px', 'borderRadius': '6px', 'borderLeft': '4px solid #ff4d4d'},
                                        children=[
                                            html.Div("3", style={'backgroundColor': '#ff4d4d', 'color': '#121212', 'borderRadius': '50%', 'width': '24px', 'height': '24px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'fontWeight': 'bold', 'marginRight': '12px'}),
                                            html.Div(style={'flex': '1'}, children=[
                                                html.H5("Approach Game: Shots from the rough", style={'margin': '0 0 3px 0', 'color': '#ffffff', 'fontSize': '14px'}),
                                                html.P("Difficulty controlling distance from non-fairway lies.", style={'margin': '0', 'color': '#888888', 'fontSize': '12px'})
                                            ]),
                                            html.Div("-1.4 SG", style={'color': '#ff4d4d', 'fontWeight': 'bold', 'fontSize': '15px'})
                                        ]
                                    ),
                                ]
                            )
                        ]
                    ),
                ]
            ),
            
            # Row 3: Smart Distances Chart & Scoring Breakdown Chart
            html.Div(
                style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '25px'},
                children=[
                    # Smart Distances Horizontal Bar Chart
                    html.Div(
                        style={'flex': '1.1', 'minWidth': '480px', 'backgroundColor': '#1e1e1e', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.3)'},
                        children=[
                            dcc.Graph(id='arccos-smart-distances-chart', figure=dist_fig)
                        ]
                    ),
                    # Scoring Breakdown Comparison
                    html.Div(
                        style={'flex': '1', 'minWidth': '450px', 'backgroundColor': '#1e1e1e', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.3)'},
                        children=[
                            dcc.Graph(id='scoring-breakdown-chart', figure=scoring_fig),
                            # Small note box
                            html.Div(
                                style={'marginTop': '15px', 'backgroundColor': '#1a1a1a', 'padding': '10px 15px', 'borderRadius': '6px', 'fontSize': '12px', 'color': '#aaaaaa'},
                                children=[
                                    html.Strong("Scoring Summary: ", style={'color': '#ff4d4d'}),
                                    "Compared to a 5 HCP player, you lose an average of ",
                                    html.Span("0.5 strokes", style={'color': '#ff4d4d'}),
                                    " per hole on Par 5s, highlighting a significant scoring bottleneck."
                                ]
                            )
                        ]
                    ),
                ]
            )
        ])
    return html.Div([html.H3("Content Not Available")])

# ==============================================================================
# 6. SINGLE-CLUB DEEP DIVE CALLBACKS
# ==============================================================================
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

# ==============================================================================
# 7. MAIN RUN STATEMENT
# ==============================================================================
if __name__ == '__main__':
    app.run(debug=True)
