# golf_app.py
# application to monitor golf statistics from Garmin and Arccos
# provide correlation with health statistics such as RHR + Avg Ball Speed
# show that as you get fitter you hit the ball further
# update from work 17/12/24
# keeping this alive as might ressurect as part of my ai prompt engineering journey
import pandas as pd
from dash import Dash, dcc, html

data = (
    pd.read_csv("garmin_data.csv")
    .query("Hole == '1' and Score == '5'")
    .assign(date=lambda data: pd.to_datetime(data["Date"], format="%Y-%m-%d"))
    .sort_values(by="Hole")
)

app = Dash(__name__)

app.layout = html.Div(
    children=[
        html.H1(children="Golf Stats Analytics"),
        html.P(
            children=(
                "application to monitor golf statistics from Garmin and Arccos"
            ),
        ),
        dcc.Graph(
            figure={
                "data": [
                    {
                        "x": data["Date"],
                        "y": data["AveragePrice"],
                        "type": "lines",
                    },
                ],
                "layout": {"title": "Average Price of Golf Balls"},
            },
        ),
        dcc.Graph(
            figure={
                "data": [
                    {
                        "x": data["Date"],
                        "y": data["Total Volume"],
                        "type": "lines",
                    },
                ],
                "layout": {"title": "Golf Balls Sold"},
            },
        ),
    ]
)

if __name__ == "__main__":
    app.run_server(debug=True)