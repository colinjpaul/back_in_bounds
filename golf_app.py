# App to query individual metrics from Launch Monitor Data and
# see trends over time

import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd

# Load data from the specific data location defined in your query [1]
# Using a raw string (r'') to properly handle the backslashes in the file path
file_path = r'data\launch_mon_feb25_26.csv'
df = pd.read_csv(file_path)

# Data preparation based on your CSV structure [1]
df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
df = df.replace('N/A', None)

# Convert key metrics to numeric for visualization [1]
for col in ['Total', 'Club Speed', 'Smash']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

app = dash.Dash(__name__)

app.layout = html.Div(style={'backgroundColor': '#121212', 'color': 'white', 'padding': '20px'}, children=[
    html.H1("Launch Monitor Performance Dashboard", style={'textAlign': 'center'}),

    html.Div([
        html.Label("Filter by Club (ai200 / Rogue ST):"),
        dcc.Dropdown(
            id='club-selector',
            options=[{'label': c, 'value': c} for c in df['Club'].unique() if c is not None],
            value='7 Iron',
            style={'color': 'black', 'width': '250px'}
        ),
    ], style={'marginBottom': '30px'}),

    html.Div([
        # Visualizes speed vs potential distance seen in Trackman sessions [1, 3]
        dcc.Graph(id='dist-speed-scatter'),
        # Tracks efficiency (Smash Factor) over time for your ai200 irons [1, 4]
        dcc.Graph(id='smash-factor-trend')
    ])
])


@app.callback(
    [Output('dist-speed-scatter', 'figure'),
     Output('smash-factor-trend', 'figure')],
    [Input('club-selector', 'value')]
)
def update_dashboard(selected_club):
    filtered_df = df[df['Club'] == selected_club].copy()

    # Chart 1: Tracking the 'engine' through Club Speed vs Total Distance [1, 2]
    fig1 = px.scatter(
        filtered_df, x='Club Speed', y='Total', color='Device',
        title=f"{selected_club}: Club Speed vs Total Distance",
        template="plotly_dark", labels={'Total': 'Total Distance (yds)'}
    )

    # Chart 2: Monitoring ball-striking quality via Smash Factor [1, 4, 5]
    fig2 = px.line(
        filtered_df.dropna(subset=['Smash']), x='Date', y='Smash', markers=True,
        title=f"{selected_club}: Efficiency (Smash Factor) Trend",
        template="plotly_dark"
    )

    return fig1, fig2


if __name__ == '__main__':
    app.run_server(debug=True)