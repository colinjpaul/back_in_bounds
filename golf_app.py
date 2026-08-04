import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd

# 1. DATA LOADING & CLEANING
file_path = r'data/launch_mon_may21_26.csv' 
df = pd.read_csv(file_path)

# Corrected date format for "06-07-24" data [3]
df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%y')

for col in ['Total', 'Club Speed', 'Smash']: 
    df[col] = pd.to_numeric(df[col], errors='coerce')

# 2. APP INITIALIZATION
# Corrected: Using double underscores (__name__) [1]
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

# 3. GLOBAL LAYOUT (Dark Theme) [1]
app.layout = html.Div(style={'backgroundColor': '#121212', 'color': 'white', 'padding': '20px', 'minHeight': '100vh'}, children=[ 
    html.H1("Back in Bounds: Golf Performance Analytics", style={'textAlign': 'center'}),
    
    dcc.Tabs(id="main-tabs", value='tab-practice', children=[
        dcc.Tab(label='Range Sessions', value='tab-practice', 
                style={'backgroundColor': '#1e1e1e', 'color': 'white'}, 
                selected_style={'backgroundColor': '#333', 'color': 'cyan'}),
        dcc.Tab(label='Course Performance', value='tab-arccos', 
                style={'backgroundColor': '#1e1e1e', 'color': 'white'}, 
                selected_style={'backgroundColor': '#333', 'color': 'cyan'}),
    ]),
    
    html.Div(id='tabs-content', style={'paddingTop': '20px'})
])

# 4. TAB CONTENT CALLBACK [1]
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
                # FIXED: Added  brackets here
                value=df['Club'].iloc[0] if not df.empty else None, 
                style={'color': 'black', 'width': '300px'} 
            ), 
            dcc.Graph(id='dist-speed-scatter'), 
            dcc.Graph(id='smash-factor-trend') 
        ])
    return html.Div([html.H3("Coming Soon")])

# 5. DATA VISUALIZATION CALLBACK [2]
@app.callback( 
    [Output('dist-speed-scatter', 'figure'), Output('smash-factor-trend', 'figure')], 
    [Input('club-selector', 'value')] 
) 
def update_dashboard(selected_club): 
    filtered_df = df[df['Club'] == selected_club].copy()
    
    fig1 = px.scatter(filtered_df, x='Club Speed', y='Total', title=f"{selected_club}: Speed vs Distance", template="plotly_dark")
    fig2 = px.line(filtered_df.dropna(subset=['Smash']), x='Date', y='Smash', title=f"{selected_club}: Smash Trend", template="plotly_dark")
    
    return fig1, fig2

# 6. RUN SERVER [2]
# Corrected: Using double underscores (__name__ and __main__)
if __name__ == '__main__': 
    app.run(debug=True)