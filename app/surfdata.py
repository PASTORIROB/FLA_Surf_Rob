import pandas as pd
from datetime import datetime

regions = {
    "north": {
        "Jacksonville Beach Pier": "41112",
        "Ponte Vedra": "41112",
        "St. Augustine Pier": "41112",
        "Ponce Inlet": "41012"
    },
    "central": {
        "New Smyrna Beach": "41012",
        "Flagler Pier": "41113"
    },
    "south": {
        "Port St. Lucie": "41114",
        "Fort Lauderdale": "41114",
        "Jupiter": "41114"
    }
}

def c_to_f(celsius):
    return round((celsius * 9/5) + 32, 1)

def m_to_ft(meters):
    return round(meters * 3.28084, 1)

def fetch_buoy_history(station_id):
    url = f"https://www.ndbc.noaa.gov/data/realtime2/{station_id}.txt"
    try:
        df = pd.read_csv(url, delim_whitespace=True, skiprows=[1,2], na_values=['MM'])
        df['Timestamp'] = pd.to_datetime(df[['#YY','MM','DD','hh','mm']].rename(columns={'#YY':'year','MM':'month','DD':'day','hh':'hour','mm':'minute'}))
        df = df[df['Timestamp'] > datetime.utcnow() - pd.Timedelta(days=3)]

        df['Wave Height (ft)'] = df['WVHT'].apply(lambda x: m_to_ft(x) if pd.notna(x) else None)
        df['Dominant Period (s)'] = df['DPD']
        df['Water Temp (°F)'] = df['WTMP'].apply(lambda x: c_to_f(x) if pd.notna(x) else None)
        df['Air Temp (°F)'] = df['ATMP'].apply(lambda x: c_to_f(x) if pd.notna(x) else None)

        return df[['Timestamp', 'Wave Height (ft)', 'Dominant Period (s)', 'Water Temp (°F)', 'Air Temp (°F)']].sort_values('Timestamp')
    except Exception as e:
        return pd.DataFrame([{'Error': str(e)}])
