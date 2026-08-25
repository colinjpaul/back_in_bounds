import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd

# 1. DATA LOADING & CLEANING
file_path = r'data/launch_mon_may21_26.csv' 
df = pd.read_csv(file_path)

# Corrected date format to handle "06-07-24" data without errors
df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%y')

# Ensuring metrics are numeric to prevent graphing crashes
for col in ['Total', 'Club Speed', 'Smash']: 
    df[col] = pd.to_numeric(df[col], errors='coerce')

# 2. GENERATE THE GLOBAL GAPPING CHART
# We build this once here so it loads instantly for all clubs combined!
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

# 3. APP INITIALIZATION (Using double underscores: __name__)
app = dash.Dash(__name__, suppress_callback_exceptions=True) 
server = app.server

# 4. GLOBAL LAYOUT (Dark Theme)
app.layout = html.Div(style={'backgroundColor': '#121212', 'color': 'white', 'padding': '20px', 'minHeight': '100vh'}, children=[ 
    html.H1("Back in Bounds: Golf Performance Analytics", style={'textAlign': 'center'}),
    
    # Navigation Tabs
    dcc.Tabs(id="main-tabs", value='tab-practice', children=[
        dcc.Tab(label='Range Sessions', value='tab-practice'),
        dcc.Tab(label='Course Performance', value='tab-arccos'),
    ]),
    
    html.Div(id='tabs-content', style={'paddingTop': '20px'})
])

# 5. TAB CONTENT CALLBACK
@app.callback(
    Output('tabs-content', 'children'), 
    Input('main-tabs', 'value') 
) 
def render_content(tab): 
    if tab == 'tab-practice': 
        return html.Div([ 
            html.H3('Practice Analytics (Launch Monitor)'),
            
            # A. INTEGRATED: Your beautiful global scatter plot goes here!
            dcc.Graph(id='global-gapping-scatter', figure=global_fig),
            
            html.Hr(style={'borderColor': '#444', 'margin': '40px 0'}),
            
            # B. DEEP DIVE: Select an individual club to see speed & strike trends
            html.H4("Single Club Deep Dive Analysis"),
            html.Label("Select Club:"), 
            dcc.Dropdown( 
                id='club-selector', 
                options=[{'label': i, 'value': i} for i in df['Club'].unique()], 
                # This must have  at the end of iloc: .iloc
                value=df['Club'].iloc[0] if not df.empty else None, 
                style={'color': 'black', 'width': '300px'} 
            ), 
            
            # The two individual-club charts (updated by the callback below)
            html.Div(style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '20px'}, children=[
                dcc.Graph(id='dist-speed-scatter', style={'flex': '1', 'minWidth': '400px'}), 
                dcc.Graph(id='smash-factor-trend', style={'flex': '1', 'minWidth': '400px'}) 
            ])
        ])
    return html.Div([html.H3(f"{tab.replace('tab-', '').title()} Metrics Coming Soon")])

# 6. DATA VISUALIZATION CALLBACK (For the Single-Club Deep Dive)
@app.callback( 
    [Output('dist-speed-scatter', 'figure'), 
     Output('smash-factor-trend', 'figure')], 
    [Input('club-selector', 'value')] 
) 
def update_dashboard(selected_club): 
    filtered_df = df[df['Club'] == selected_club].copy()
    
    fig1 = px.scatter(
        filtered_df, x='Club Speed', y='Total', 
        title=f"{selected_club}: Speed vs Distance", 
        template="plotly_dark"
    )
    
    fig2 = px.line(
        filtered_df.dropna(subset=['Smash']), x='Date', y='Smash', 
        title=f"{selected_club}: Smash Factor Trend", 
        template="plotly_dark"
    )
    
    return fig1, fig2

# 7. RUN SERVER (Using double underscores: __name__ and __main__)
if __name__ == '__main__': 
    app.run(debug=True)