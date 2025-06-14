from flask import Flask, render_template, request
from surfdata import regions, fetch_buoy_history, generate_comparison_chart, forecast_wave_heights

app = Flask(__name__)

@app.route('/')
def index():
    selected_region = request.args.get('region', 'central')
    data_by_location = {}

    for loc, station in regions[selected_region].items():
        df = fetch_buoy_history(station)
        data_by_location[loc] = df.to_dict(orient='records')

    chart_url, full_df = generate_comparison_chart()

    latest_waves = full_df.sort_values('Timestamp').groupby('Location').last()
    top_location = latest_waves['Wave Height (ft)'].idxmax()

    return render_template("index.html", region=selected_region, data=data_by_location, chart_url=chart_url, top_location=top_location)

@app.route('/forecast')
def forecast():
    chart_url, results = forecast_wave_heights()
    return render_template("forecast.html", chart_url=chart_url, results=results)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
