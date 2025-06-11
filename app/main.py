from flask import Flask, render_template, request
from surfdata import regions, fetch_buoy_history

app = Flask(__name__)

@app.route('/')
def index():
    selected_region = request.args.get('region', 'central')
    data_by_location = {}

    for loc, station in regions[selected_region].items():
        df = fetch_buoy_history(station)
        data_by_location[loc] = df.to_dict(orient='records')

    return render_template("index.html", region=selected_region, data=data_by_location)

if __name__ == '__main__':
    app.run(debug=True)
