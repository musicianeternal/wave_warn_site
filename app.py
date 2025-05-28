from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache

from satellite_module.satellite_data import get_satellite_forecast
from utils.summaries import generate_summaries

app = Flask(
    __name__,
    static_folder="static",
    static_url_path="/static",
    template_folder="templates"
)
CORS(app)
limiter = Limiter(app, key_func=get_remote_address, default_limits=["100 per minute"])
app.config["CACHE_TYPE"] = "simple"
cache = Cache(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/forecast", methods=["POST"])
@limiter.limit("10/second")
@cache.cached(timeout=300, key_prefix=lambda: request.get_data())
def forecast():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    try:
        lat = float(data.get("latitude"))
        lon = float(data.get("longitude"))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid or missing latitude/longitude"}), 400

    try:
        payload = get_satellite_forecast(lat, lon)
        weather = payload["weather"]
        density = payload["cloud_density"]
        summaries = generate_summaries(weather)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "satellite_density": density,
        "forecast": weather,
        "summaries": summaries
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5002)
