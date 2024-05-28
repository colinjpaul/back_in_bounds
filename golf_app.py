# golf_app.py

import pandas as pd
from dash import Dash, dcc, html

data = (
    pd.read_csv("garmin_data.csv")
    .query("Hole == '1' and score == ''")
    .assign(date=lambda data: pd.to_datetime(data["Date"], format="%Y-%m-%d"))
    .sort_values(by="Date")
)