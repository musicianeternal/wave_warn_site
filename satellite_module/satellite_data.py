import os
import ee
import datetime
import requests

# Earth Engine setup
EE_PROJECT = "ee-2864"  # replace with your own project ID

def _init_ee():
    try:
        ee.Initialize(project=EE_PROJECT)
    except ee.EEException:
        ee.Authenticate()
        ee.Initialize(project=EE_PROJECT)

_init_ee()

# OpenWeatherMap key
API_KEY = os.getenv("OPENWEATHERMAP_KEY", "892dc747a40aff2fc21d588ab365bfd5")
if not API_KEY:
    raise RuntimeError("OPENWEATHERMAP_KEY not set")

def get_satellite_cloud_density(lon, lat):
    """
    Fetch average cloud probability from Sentinel-2 for the given coordinates.
    Returns a float (0–100) or None on error.
    """
    try:
        region = ee.Geometry.Point([lon, lat])
        year = datetime.datetime.now().year

        collection = (
            ee.ImageCollection("COPERNICUS/S2_CLOUD_PROBABILITY")
              .filterDate(f"{year}-01-01", f"{year}-12-31")
              .filterBounds(region)
              .map(lambda img: img.clip(region))
        )
        mean_prob = collection.select("probability").mean()
        stats = mean_prob.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=region,
            scale=100,
            maxPixels=1e13
        ).getInfo()

        return round(stats.get("probability", 0), 2)
    except Exception as e:
        print("Error in get_satellite_cloud_density:", e)
        return None

def get_forecast_data(lat, lon):
    """
    Fetch current, hourly & daily data from OpenWeatherMap One Call API 3.0.
    Returns the JSON response dict, or {} on error.
    """
    url = (
        "https://api.openweathermap.org/data/3.0/onecall"
        f"?lat={lat}&lon={lon}"
        "&exclude=minutely,alerts"
        f"&appid={API_KEY}&units=metric"
    )
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print("Error in get_forecast_data:", e)
        return {}

def get_satellite_forecast(lat, lon):
    """
    Combine satellite cloud density with weather forecast.
    Returns:
      {
        "current_cloud_density": float or None,
        "forecast": { ... OpenWeatherMap JSON ... }
      }
    """
    print(f"Fetching forecast for lat={lat}, lon={lon}")
    density = get_satellite_cloud_density(lon, lat)
    forecast = get_forecast_data(lat, lon)
    return {
        "current_cloud_density": density,
        "forecast": forecast
    }
