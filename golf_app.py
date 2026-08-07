import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd

# 1. DATA LOADING & CLEANING
# Updated to use the May 21st data session from your latest source [1]
file_path = r'data/launch_mon_may21_26.csv' 
df = pd.read_csv(file_path)

# Corrected date format to handle "06-07-24" data without errors [1]
df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%y')

# Ensuring metrics are numeric to prevent graphing crashes [1]
for col in ['Total', 'Club Speed', 'Smash']: 
    df[col] = pd.to_numeric(df[col], errors='coerce')

# 2. APP INITIALIZATION
app = dash.Dash(__name__, suppress_callback_exceptions=True) 

# Required for hosting on Render via Gunicorn [1]
server = app.server

# 3. GLOBAL LAYOUT (Dark Theme)
app.layout = html.Div(style={'backgroundColor': '#121212', 'color': 'white', 'padding': '20px', 'minHeight': '100vh'}, children=[ 
    html.H1("Back in Bounds: Golf Performance Analytics", style={'textAlign': 'center'}),

    # Navigation Tabs for multi-page functionality
    dcc.Tabs(id="main-tabs", value='tab-practice', children=[
        dcc.Tab(label='Range Sessions', value='tab-practice'),
        dcc.Tab(label='Course Performance', value='tab-arccos'),
        dcc.Tab(label='Physics Simulation', value='tab-sim'),
    ]),

    html.Div(id='tabs-content', style={'paddingTop': '20px'})
])

# 4. TAB CONTENT CALLBACK
@app.callback(
    Output('tabs-content', 'children'), 
    Input('main-tabs', 'value') 
) 
def render_content(tab): 
    if tab == 'tab-practice': 
        return html.Div([ 
            html.H3('Practice Analytics (Launch Monitor)'),
            html.Label("Select Club:"), 
            dcc.Dropdown( 
                id='club-selector', 
                options=[{'label': i, 'value': i} for i in df['Club'].unique()], 
                value=df['Club'].iloc[0] if not df.empty else None, 
                style={'color': 'black', 'width': '300px'} 
            ), 
            dcc.Graph(id='dist-speed-scatter'), 
            dcc.Graph(id='smash-factor-trend') 
        ])  # <-- trailing comma removed so this returns a Div, not a 1-item tuple

    elif tab == 'tab-arccos':
        return html.Div([
            html.H3('Course Performance (Arccos Insights)', style={'color': 'cyan'}),

            # 1. KPI Cards for Strokes Gained Breakdown
            html.Div(style={'display': 'flex', 'justifyContent': 'space-around', 'padding': '20px'}, children=[
                html.Div([html.H4("Overall SG"), html.H2("-6.0", style={'color': 'red'})], style={'textAlign': 'center'}),
                html.Div([html.H4("Driving"), html.H2("-1.1")], style={'textAlign': 'center'}),
                html.Div([html.H4("Approach"), html.H2("-3.9", style={'color': 'red'})], style={'textAlign': 'center'}),
                html.Div([html.H4("Short"), html.H2("+0.8", style={'color': 'green'})], style={'textAlign': 'center'}),
                html.Div([html.H4("Putting"), html.H2("-1.9")], style={'textAlign': 'center'}),
            ]),

            # 2. Top Insights & Scoring Breakdown Row
            html.Div(style={'display': 'flex'}, children=[
                # Top 3 Insights Panel
                html.Div(style={'width': '50%', 'padding': '10px'}, children=[
                    html.H4("Top 3 Insights to Improve"),
                    html.Ul([
                        html.Li("Putting: -2.0 SG on 0-10 ft putts"),
                        html.Li("Approach: -1.5 SG on 100-150 yard shots"),
                        html.Li("Approach: -1.4 SG on shots from the rough"),
                    ])
                ]),
                # Scoring Averages Chart
                html.Div(style={'width': '50%'}, children=[
                    dcc.Graph(
                        figure=px.bar(
                            x=['Par 3s', 'Par 4s', 'Par 5s'],
                            y=[3.7, 4.8, 5.7],
                            title="Scoring Averages",
                            template="plotly_dark"
                        ).update_traces(marker_color='cyan')
                    )
                ])
            ]),

            # 3. Smart Distances (Visualization of Source 4)
            html.H4("Arccos Smart Distances (Yds)"),
            dcc.Graph(
                figure=px.bar(
                    # TODO: replace with your real Arccos smart-distance numbers,
                    # in the same order as the club list below.
                    x=[220, 195, 165, 155, 145, 135, 125, 105, 95, 80, 65, 55],
                    y=['Dr', '5w', '5i', '6i', '7i', '8i', '9i', 'PW', 'Aw', '50°', '54°', '58°'],
                    orientation='h',
                    template="plotly_dark",
                    labels={'x': 'Distance (Yards)', 'y': 'Club'}
                ).update_layout(yaxis={'categoryorder': 'total ascending'})
            )
        ])

    else:
        return html.Div([html.H3(f"{tab.replace('tab-', '').title()} Metrics Coming Soon")])

# 5. DATA VISUALIZATION CALLBACK
@app.callback( 
    [Output('dist-speed-scatter', 'figure'), 
     Output('smash-factor-trend', 'figure')], 
    [Input('club-selector', 'value')] 
) 
def update_dashboard(selected_club): 
    # Filtering data based on the selected club [3]
    filtered_df = df[df['Club'] == selected_club].copy()
    
    # Chart 1: Speed vs Distance
    fig1 = px.scatter(
        filtered_df, x='Club Speed', y='Total', 
        title=f"{selected_club}: Speed vs Distance", 
        template="plotly_dark"
    )
    
    # Chart 2: Efficiency (Smash Factor) over time
    fig2 = px.line(
        filtered_df.dropna(subset=['Smash']), x='Date', y='Smash', 
        title=f"{selected_club}: Smash Factor Trend", 
        template="plotly_dark"
    )
    
    return fig1, fig2

# 6. RUN SERVER
if __name__ == '__main__': 
    app.run(debug=True)