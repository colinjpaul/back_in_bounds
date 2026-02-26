import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px


# 1. Data Preparation (Based on Source Ledger)
def load_golf_data():
    # In a real scenario, this would be: data = pd.read_csv("launch_mon_data.csv")
    # For this template, we represent the source structure:
    raw_data = [
        ["6-7-24", "Driver", "Rogue ST Max", 236, 96, 143, None],
        ["4-1-25", "7 Iron", "ai200 '25", 169, 79, 114, None],
        ["2-2-25", "5 Iron", "ai200 '25", 200, 86, 128, None],
        ["26-6-25", "7 Iron", "ai200 '25", 166, 82, 116, 1.4],
        ["23-12-25", "5 Iron", "ai200 '25", 203, 84, 130, None],
        ["23-12-25", "9 iron", "ai200 '25", 150, 81, 106, None],
    ]

    columns = ["Date", "Club", "Model", "Carry Distance", "Club Speed", "Ball Speed", "Smash"]
    df = pd.DataFrame(raw_data, columns=columns)

    # Convert Date to datetime - handling the D-M-YY format in sources [1, 2]
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)

    # Ensure numeric columns are floats, coercing "N/A" or "NR" to NaN [2]
    numeric_cols = ["Carry Distance", "Club Speed", "Ball Speed", "Smash"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df.sort_values("Date")


df = load_golf_data()

# 2. App Layout
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Golf Performance & Trend Analytics"),

    html.Div([
        html.Div([
            html.Label("Select Club:"),
            dcc.Dropdown(
                id='club-filter',
                options=[{'label': i, 'value': i} for i in df['Club'].unique()],
                value=df['Club'].unique()
            ),
        ], style={'width': '48%', 'display': 'inline-block'}),

        html.Div([
            html.Label("Select Metric:"),
            dcc.Dropdown(
                id='metric-filter',
                options=[
                    {'label': 'Carry Distance', 'value': 'Carry Distance'},
                    {'label': 'Club Speed', 'value': 'Club Speed'},
                    {'label': 'Smash Factor', 'value': 'Smash'}
                ],
                value='Carry Distance'
            ),
        ], style={'width': '48%', 'float': 'right', 'display': 'inline-block'}),
    ], style={'padding': '20px'}),

    dcc.Graph(id='trend-graph'),

    html.Div(id='stats-summary', style={'padding': '20px', 'fontSize': '18px'})
])


# 3. Interactivity (Callbacks)
@app.callback(
    [Output('trend-graph', 'figure'),
     Output('stats-summary', 'children')],
    [Input('club-filter', 'value'),
     Input('metric-filter', 'value')]
)
def update_graph(selected_club, selected_metric):
    # Filter data for the specific club [3, 4]
    filtered_df = df[df['Club'] == selected_club].dropna(subset=[selected_metric])

    # Create Trend Visualisation
    fig = px.scatter(
        filtered_df,
        x="Date",
        y=selected_metric,
        trendline="lowess",  # Adds the trend data over time
        title=f"{selected_metric} Progress for {selected_club}",
        labels={selected_metric: f"{selected_metric} Value", "Date": "Session Date"},
        template="plotly_white"
    )

    # Calculate performance stats
    avg_val = filtered_df[selected_metric].mean()
    max_val = filtered_df[selected_metric].max()

    summary = f"Average {selected_metric}: {avg_val:.1f} | Personal Best: {max_val:.1f}"

    return fig, summary


if __name__ == '__main__':
    app.run_server(debug=True)