# golf_app.py
# application to monitor golf statistics from Garmin and Arccos
# provide correlation with health statistics such as RHR + Avg Ball Speed
# show that as you get fitter you hit the ball further
# update 22-10-25
import pandas as pd
from dash import Dash, dcc, html

data = (
    pd.read_csv("garmin_data.csv")
    .assign(Date=lambda data: pd.to_datetime(data["Date"], format="%Y-%m-%d"))
    .sort_values(by="Date")
)