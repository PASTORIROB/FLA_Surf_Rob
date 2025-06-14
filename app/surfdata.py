import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
from io import BytesIO
import base64
from sklearn.linear_model import LinearRegression
import numpy as np

regions = {
    "north": {
        "Jacksonville Beach Pier": "41112",
    },
    "central": {
        "New Smyrna Beach": "41113"
    },
    "south": {
        "Fort Lauderdale Beach": "41114",
    }
}

def c_to_f(celsius):
    return round((celsius * 9/5) + 32, 1)

def m_to_ft(meters):
    return round(meters * 3.28084, 1)

def fetch_buoy_history(station_id):
    url = f"https://www.ndbc.noaa.gov/data/realtime2/{station_id}.txt"
    try:
        df = pd.read_csv(url, sep=r'\s+', skiprows=[1,2], na_values=['MM'])
        df['Timestamp'] = pd.to_datetime(df[['#YY','MM','DD','hh','mm']].rename(columns={'#YY':'year','MM':'month','DD':'day','hh':'hour','mm':'minute'}))
        df = df[df['Timestamp'] > datetime.utcnow() - pd.Timedelta(days=3)]

        df['Wave Height (ft)'] = df['WVHT'].apply(lambda x: m_to_ft(x) if pd.notna(x) else None)
        df['Dominant Period (s)'] = df['DPD']
        df['Water Temp (°F)'] = df['WTMP'].apply(lambda x: c_to_f(x) if pd.notna(x) else None)
        df['Air Temp (°F)'] = df['ATMP'].apply(lambda x: c_to_f(x) if pd.notna(x) else None)

        return df[['Timestamp', 'Wave Height (ft)', 'Dominant Period (s)', 'Water Temp (°F)', 'Air Temp (°F)']].sort_values('Timestamp', ascending=False)
    except Exception as e:
        return pd.DataFrame([{'Error': str(e)}])

def generate_comparison_chart():
    combined_df = pd.DataFrame()
    for region, locs in regions.items():
        for loc, station in locs.items():
            df = fetch_buoy_history(station)
            df['Location'] = loc
            combined_df = pd.concat([combined_df, df], ignore_index=True)

    fig = go.Figure()
    colors = ['blue', 'green', 'purple']
    for i, loc in enumerate(combined_df['Location'].unique()):
        subset = combined_df[combined_df['Location'] == loc]
        fig.add_trace(go.Scatter(x=subset['Timestamp'], y=subset['Wave Height (ft)'], mode='lines', name=loc, line=dict(color=colors[i])))

    fig.update_layout(title="Wave Height Comparison (Past 3 Days)", xaxis_title="Time", yaxis_title="Wave Height (ft)", template="plotly_dark", legend=dict(orientation="h", y=-0.3), margin=dict(t=40, b=40, l=40, r=40))

    img_bytes = fig.to_image(format="png")
    base64_img = base64.b64encode(img_bytes).decode('utf-8')
    return f"data:image/png;base64,{base64_img}", combined_df

def forecast_wave_heights():
    forecast_horizon = 12
    prediction_results = []

    fig = go.Figure()
    colors = ['blue', 'green', 'purple']

    for i, (region, locs) in enumerate(regions.items()):
        for loc, station in locs.items():
            df = fetch_buoy_history(station)
            df = df[['Timestamp', 'Wave Height (ft)']].dropna()
            df['TimestampOrdinal'] = df['Timestamp'].map(datetime.toordinal) + df['Timestamp'].dt.hour / 24
            X = df['TimestampOrdinal'].values.reshape(-1, 1)
            y = df['Wave Height (ft)'].values
            if len(X) < 10:
                continue
            model = LinearRegression().fit(X, y)
            last_timestamp = df['Timestamp'].max()
            future_hours = [last_timestamp + pd.Timedelta(hours=h) for h in range(1, forecast_horizon + 1)]
            X_future = [ts.toordinal() + ts.hour / 24 for ts in future_hours]
            y_pred = model.predict(np.array(X_future).reshape(-1, 1))
            fig.add_trace(go.Scatter(x=future_hours, y=y_pred, mode='lines+markers', name=f"{loc} Forecast", line=dict(dash='dash', color=colors[i])))
            fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['Wave Height (ft)'], mode='lines', name=f"{loc} History", line=dict(color=colors[i])))
            prediction_results.append((loc, round(float(y_pred[-1]), 2)))

    fig.update_layout(title="Wave Height Forecast (Next 12 Hours)", xaxis_title="Time", yaxis_title="Wave Height (ft)", template="plotly_dark", margin=dict(t=40, b=40, l=40, r=40), legend=dict(orientation="h", y=-0.2))

    img_bytes = fig.to_image(format="png")
    base64_img = base64.b64encode(img_bytes).decode('utf-8')
    return f"data:image/png;base64,{base64_img}", prediction_results
