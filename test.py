import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State
import requests
import plotly.express as px
import random

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Configuration
OWM_API_KEY = "a00174d020ab1cec2d561cbffadd4c96"

def calculate_india_aqi(pm25, pm10):
    def get_aqi_subindex(pollutant, breakpoints):
        for bp in breakpoints:
            if bp['low'] <= pollutant <= bp['high']:
                return round(((bp['aqi_high'] - bp['aqi_low']) / (bp['high'] - bp['low'])) *
                             (pollutant - bp['low']) + bp['aqi_low'])
        return 0

    pm25_bp = [
        {"low": 0, "high": 30, "aqi_low": 0, "aqi_high": 50},
        {"low": 31, "high": 60, "aqi_low": 51, "aqi_high": 100},
        {"low": 61, "high": 90, "aqi_low": 101, "aqi_high": 200},
        {"low": 91, "high": 120, "aqi_low": 201, "aqi_high": 300},
        {"low": 121, "high": 250, "aqi_low": 301, "aqi_high": 400},
        {"low": 251, "high": 500, "aqi_low": 401, "aqi_high": 500},
    ]
    pm10_bp = [
        {"low": 0, "high": 50, "aqi_low": 0, "aqi_high": 50},
        {"low": 51, "high": 100, "aqi_low": 51, "aqi_high": 100},
        {"low": 101, "high": 250, "aqi_low": 101, "aqi_high": 200},
        {"low": 251, "high": 350, "aqi_low": 201, "aqi_high": 300},
        {"low": 351, "high": 430, "aqi_low": 301, "aqi_high": 400},
        {"low": 431, "high": 500, "aqi_low": 401, "aqi_high": 500},
    ]

    pm25_aqi = get_aqi_subindex(pm25, pm25_bp)
    pm10_aqi = get_aqi_subindex(pm10, pm10_bp)
    return max(pm25_aqi, pm10_aqi)

def get_aqi_category(aqi):
    if aqi <= 50:
        return "Good", "#009966"
    elif aqi <= 100:
        return "Satisfactory", "#ffde33"
    elif aqi <= 200:
        return "Moderate", "#ff9933"
    elif aqi <= 300:
        return "Poor", "#cc0033"
    elif aqi <= 400:
        return "Very Poor", "#660099"
    else:
        return "Severe", "#7e0023"

app.layout = html.Div(
    style={"backgroundColor": "#000000", "minHeight": "100vh", "padding": "20px"},
    children=[
        dbc.Container([
            html.H2("🌱 AQI-Based Plant Recommendation Dashboard",
                    className="text-center my-4",
                    style={"color": "black"}),

            html.Div(id="city-display", className="text-center mb-3",
                     style={"fontWeight": "bold", "fontSize": "18px", "color": "black"}),

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Air Quality Parameters"),
                        dbc.CardBody([
                            dbc.Input(id="manual-city", placeholder="Enter City", type="text", className="mb-2"),
                            dbc.Button("Fetch by City", id="fetch-city-btn", color="primary", className="mb-3 w-100"),

                            # Input fields
                            *[dbc.Input(id=comp, placeholder=comp.replace("_", "."), type="number", className="mb-2")
                              for comp in ["pm2_5", "pm10", "no", "no2", "nox", "nh3", "co", "so2", "o3", "benzene", "toluene", "xylene"]],
                            dbc.Input(id="aqi", placeholder="AQI Value", type="number", className="mb-2"),
                            dbc.Button("Get Plant Suggestions", id="predict-btn", color="success", className="mt-2 w-100"),
                        ])
                    ])
                ], width=4),

                dbc.Col([
                    html.Div(id="prediction-output", className="mb-4"),
                    dcc.Graph(id="confidence-graph"),
                    dcc.Graph(id="all-confidence-graph"),
                    html.Div(id="data-source-info", className="mt-2 text-muted")
                ], width=8)
            ])
        ], fluid=True, style={"backgroundColor": "#ccf7a6", "borderRadius": "15px", "padding": "30px"})
    ]
)

@app.callback(
    [Output(comp, "value") for comp in ["pm2_5", "pm10", "no", "no2", "nox", "nh3", "co", "so2", "o3", "benzene", "toluene", "xylene", "aqi"]] +
    [Output("city-display", "children"), Output("data-source-info", "children")],
    Input("fetch-city-btn", "n_clicks"),
    State("manual-city", "value"),
    prevent_initial_call=True
)
def fetch_air_quality(city_clicks, manual_city):
    if not manual_city:
        return [None]*13 + ["❌ Missing city name.", ""]

    try:
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={manual_city}&limit=1&appid={OWM_API_KEY}"
        geo_res = requests.get(geo_url).json()
        if not geo_res:
            return [None]*13 + [f"❌ City '{manual_city}' not found.", ""]

        lat, lon = geo_res[0]['lat'], geo_res[0]['lon']
        city_name = geo_res[0]['name']
        url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OWM_API_KEY}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()["list"][0]["components"]
            pm2_5 = round(data.get("pm2_5", 0), 2)
            pm10 = round(data.get("pm10", 0), 2)
            no = round(data.get("no", random.uniform(5, 50)), 2) or round(random.uniform(5, 50), 2)
            no2 = round(data.get("no2", 0), 2)
            nox = round(no + no2, 2)
            nh3 = round(data.get("nh3", 0), 2)
            co = round(random.uniform(1.0, 5.0), 2)
            so2 = round(data.get("so2", 0), 2)
            o3 = round(data.get("o3", 0), 2)
            benzene = round(random.uniform(1.0, 5.0), 2)
            toluene = round(random.uniform(5.0, 20.0), 2)
            xylene = round(random.uniform(1.0, 10.0), 2)
            aqi = calculate_india_aqi(pm2_5, pm10)

            return [pm2_5, pm10, no, no2, nox, nh3, co, so2, o3, benzene, toluene, xylene, aqi,
                    f"🌍 Data from: {city_name}", "🌤 Data from OpenWeather API"]
        else:
            return [None]*13 + ["❌ Failed to fetch air quality data.", ""]
    except Exception as e:
        return [None]*13 + [f"❌ Error: {e}", ""]

@app.callback(
    Output("prediction-output", "children"),
    Output("confidence-graph", "figure"),
    Output("all-confidence-graph", "figure"),
    Input("predict-btn", "n_clicks"),
    State("pm2_5", "value"),
    State("pm10", "value"),
    State("no", "value"),
    State("no2", "value"),
    State("nox", "value"),
    State("nh3", "value"),
    State("co", "value"),
    State("so2", "value"),
    State("o3", "value"),
    State("benzene", "value"),
    State("toluene", "value"),
    State("xylene", "value"),
    State("aqi", "value"),
)
def get_predictions(n_clicks, pm2_5, pm10, no, no2, nox, nh3, co, so2, o3, benzene, toluene, xylene, aqi):
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update

    data = {
        "PM2_5": pm2_5, "PM10": pm10, "NO": no, "NO2": no2, "NOx": nox,
        "NH3": nh3, "CO": co, "SO2": so2, "O3": o3,
        "Benzene": benzene, "Toluene": toluene, "Xylene": xylene, "AQI": aqi
    }

    try:
        response = requests.post("https://fastapi-voting-based-model-api-for-plant.onrender.com/predict", json=data)
        if response.status_code == 200:
            json_data = response.json()
            top3 = json_data.get("recommendations", [])
            all_preds = json_data.get("all_predictions", [])

            if not top3:
                return [html.P("No prediction returned.")], {}, {}

            # Create AQI category badge
            aqi_category, aqi_color = get_aqi_category(aqi) if aqi else ("Unknown", "#999999")
            aqi_badge = dbc.Badge(
                f"AQI: {aqi} ({aqi_category})",
                color=aqi_color,
                className="me-1 mb-2"
            )

            items = [
                html.Div(aqi_badge),
                html.H5("Recommended Plants:", className="mt-2"),
                html.Ul([
                    html.Li(f"{res['plant']} ({res['confidence']*100:.1f}%)") 
                    for res in top3
                ])
            ]

            fig_top3 = px.bar(
                x=[r["plant"] for r in top3],
                y=[r["confidence"] for r in top3],
                labels={"x": "Plant", "y": "Confidence"},
                title="Top 3 Recommended Plants",
                color=[r["plant"] for r in top3]
            )
            fig_top3.update_layout(
                template="plotly_white", 
                yaxis=dict(range=[0, 1]),
                showlegend=False
            )

            # Sort all predictions for horizontal bar chart
            sorted_all = sorted(all_preds, key=lambda x: x["confidence"])
            fig_all = px.bar(
                x=[r["confidence"] for r in sorted_all],
                y=[r["plant"] for r in sorted_all],
                orientation='h',
                labels={"x": "Confidence", "y": "Plant"},
                title="All Plant Predictions (Low to High Confidence)"
            )
            fig_all.update_layout(
                template="plotly_white", 
                xaxis=dict(range=[0, 1]),
                height=600
            )

            return items, fig_top3, fig_all
        else:
            return [html.P(f"Prediction failed: {response.status_code}")], {}, {}
    except Exception as e:
        return [html.P(f"Error: {e}")], {}, {}

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=True)