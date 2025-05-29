import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from satellite_module.satellite_data import get_satellite_forecast
from utils.summaries import generate_summaries

app = Flask(__name__)
CORS(app)

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"]
)
limiter.init_app(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/forecast", methods=["POST"])
@limiter.limit("10/second")
def forecast():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    try:
        lat = float(data.get("latitude"))
        lon = float(data.get("longitude"))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid or missing latitude/longitude"}), 400

    result = get_satellite_forecast(lat, lon)
    if not result.get("forecast"):
        return jsonify({"error": "Forecast data not available"}), 500

    try:
        summaries = generate_summaries(result)
    except Exception as e:
        return jsonify({"error": f"Summary error: {e}"}), 500

    return jsonify({
        "forecast": result["forecast"],
        "summaries": summaries
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, host="0.0.0.0", port=port)
