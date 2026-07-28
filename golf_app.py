import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd

# 1. DATA LOADING & CLEANING
# Using the path from your sources [2]
file_path = r'data/launch_mon_apr03_26.csv'
df = pd.read_csv(file_path)

# Fixing the UserWarning by explicitly defining the date format [5, History]
df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y') 

# Handling N/A values and numeric conversion [2, 3]
# Use %y (lowercase) for 2-digit years like '24'
# Use %y (lowercase) for 2-digit years and match the dashes in your data
df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%y')# Use %y (lowercase) for 2-digit years and match the dashes in your data
for col in ['Total', 'Club Speed', 'Smash']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# 2. APP INITIALIZATION
# suppress_callback_exceptions=True is needed for the multi-tab structure
app = dash.Dash(__name__, suppress_callback_exceptions=True)

# 3. GLOBAL LAYOUT (Dark Theme) [3]
app.layout = html.Div(style={'backgroundColor': '#121212', 'color': 'white', 'padding': '20px', 'minHeight': '100vh'}, children=[
    html.H1("Back in Bounds: Golf Performance Analytics", style={'textAlign': 'center'}),
    
    dcc.Tabs(id="main-tabs", value='tab-practice', children=[
        dcc.Tab(label='Range Sessions', value='tab-practice', 
                style={'backgroundColor': '#1e1e1e', 'color': 'white'}, 
                selected_style={'backgroundColor': '#333', 'color': 'cyan'}),
        dcc.Tab(label='Course Performance (Arccos)', value='tab-arccos', 
                style={'backgroundColor': '#1e1e1e', 'color': 'white'}, 
                selected_style={'backgroundColor': '#333', 'color': 'cyan'}),
        dcc.Tab(label='Physics Simulation Engine', value='tab-sim', 
                style={'backgroundColor': '#1e1e1e', 'color': 'white'}, 
                selected_style={'backgroundColor': '#333', 'color': 'cyan'}),
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
                value=df['Club'].iloc if not df.empty else None,
                style={'color': 'black', 'width': '300px'}
            ),
            dcc.Graph(id='dist-speed-scatter'),
            dcc.Graph(id='smash-factor-trend')
        ])
    
    elif tab == 'tab-arccos':
        return html.Div([
            html.H3('On-Course Performance (Arccos)'),
            html.P("This tab will soon integrate your -6.0 SG total and Smart Distance metrics."),
            # Future home for arccos_smart_dist_300626 analysis [4]
        ])
    
    elif tab == 'tab-sim':
        return html.Div([
            html.H3('3D Physics Engine'),
            html.P("Future home for the 3D Pro-Tracer using your 148.5 mph ball speed baseline."),
            # Future home for environmental inputs (Wind, Temp, Elevation)
        ])

# 5. DATA VISUALIZATION CALLBACK (Range Sessions) [3]
@app.callback(
    [Output('dist-speed-scatter', 'figure'),
     Output('smash-factor-trend', 'figure')],
    [Input('club-selector', 'value')]
)
def update_dashboard(selected_club):
    filtered_df = df[df['Club'] == selected_club].copy()

    # Chart 1: Club Speed vs Total Distance [3]
    fig1 = px.scatter(
        filtered_df, x='Club Speed', y='Total', color='Device',
        title=f"{selected_club}: Club Speed vs Total Distance",
        template="plotly_dark", labels={'Total': 'Total Distance (yds)'}
    )

    # Chart 2: Efficiency (Smash Factor) Trend [3]
    fig2 = px.line(
        filtered_df.dropna(subset=['Smash']), x='Date', y='Smash', markers=True,
        title=f"{selected_club}: Efficiency (Smash Factor) Trend",
        template="plotly_dark"
    )

    return fig1, fig2

# 6. RUN SERVER [5]
if __name__ == '__main__':
    app.run_server(debug=True)