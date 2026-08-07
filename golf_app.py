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
# Fixed: Replaced asterisks from source [1] with double underscores (__name__)
app = dash.Dash(__name__, suppress_callback_exceptions=True) 

# Required for hosting on Render via Gunicorn [1]
server = app.server

# 3. GLOBAL LAYOUT (Dark Theme)
app.layout = html.Div(style={'backgroundColor': '#121212', 'color': 'white', 'padding': '20px', 'minHeight': '100vh'}, children=[ 
    html.H1("Back in Bounds: Golf Performance Analytics", style={'textAlign': 'center'}), # [2]
    
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
            html.H3('Practice Analytics (Launch Monitor)'), # [2]
            html.Label("Select Club:"), 
            dcc.Dropdown( 
                id='club-selector', 
                options=[{'label': i, 'value': i} for i in df['Club'].unique()], 
                # FIXED: Added  brackets here to return a string instead of an object [2]
                value=df['Club'].iloc if not df.empty else None, 
                style={'color': 'black', 'width': '300px'} 
            ), 
            dcc.Graph(id='dist-speed-scatter'), 
            dcc.Graph(id='smash-factor-trend') 
        ])
    return html.Div([html.H3(f"{tab.replace('tab-', '').title()} Metrics Coming Soon")]) # [2]

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
# Fixed: Replaced asterisks from source [3] with double underscores (__name__ and __main__)
if __name__ == '__main__': 
    app.run(debug=True)