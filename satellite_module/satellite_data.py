import os
import requests

API_KEY = os.environ.get(
    "OPENWEATHERMAP_KEY",
    "892dc747a40aff2fc21d588ab365bfd5"
)

def get_forecast_data(lat, lon):
    """Fetch 10-day forecast from OpenWeatherMap One Call 3.0."""
    url = (
        f"https://api.openweathermap.org/data/3.0/onecall"
        f"?lat={lat}&lon={lon}"
        f"&exclude=minutely,alerts&appid={API_KEY}&units=metric"
    )
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("⚠️ Forecast fetch error:", e)
        return {}

def get_satellite_forecast(lat, lon):
    """Return only the OpenWeatherMap forecast payload."""
    forecast = get_forecast_data(lat, lon)
    return {"forecast": forecast}
