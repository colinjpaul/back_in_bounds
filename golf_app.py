# golf_app.py
# application to monitor golf statistics from Garmin and Arccos
# provide correlation with health statistics such as RHR + Avg Ball Speed
# show that has you get fitter you hit the ball further
# update from work 17/12/24
import pandas as pd
from dash import Dash, dcc, html

data = (
    pd.read_csv("garmin_data.csv")
    .query("Hole == '1' and Score == '5'")
    #.assign(date=lambda data: pd.to_datetime(data["Date"], format="%Y-%m-%d"))
    .sort_values(by="Hole")
)

app = Dash(__name__)

app.layout = html.Div(
#      children=[
#          html.H1(children="Golf Stats Analytics"),
# #         html.P(
# #             children=(
# #                 "Analyze the behavior of avocado prices and the number"
# #                 " of avocados sold in the US between 2015 and 2018"
# #             ),
# #         ),
# #         dcc.Graph(
# #             figure={
# #                 "data": [
# #                     {
# #                         "x": data["Date"],
# #                         "y": data["AveragePrice"],
# #                         "type": "lines",
# #                     },
# #                 ],
# #                 "layout": {"title": "Average Price of Avocados"},
# #             },
# #         ),
# #         dcc.Graph(
# #             figure={
# #                 "data": [
# #                     {
# #                         "x": data["Date"],
# #                         "y": data["Total Volume"],
# #                         "type": "lines",
# #                     },
# #                 ],
# #                 "layout": {"title": "Avocados Sold"},
# #             },
# #         ),
# #     ]
)

if __name__ == "__main__":
    app.run_server(debug=True)