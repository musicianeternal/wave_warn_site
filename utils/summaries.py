from datetime import datetime

def calculate_heat_index(temp_c, humidity):
    """
    Calculate the heat index using temperature (°C) and relative humidity (%).
    Converts to Fahrenheit, applies NOAA's heat index formula, then converts back to Celsius.
    """
    T = (temp_c * 9/5) + 32
    RH = humidity
    HI = (
        -42.379 +
        2.04901523 * T +
        10.14333127 * RH -
        0.22475541 * T * RH -
        0.00683783 * T**2 -
        0.05481717 * RH**2 +
        0.00122874 * T**2 * RH +
        0.00085282 * T * RH**2 -
        0.00000199 * T**2 * RH**2
    )
    HI_c = (HI - 32) * 5/9
    return HI_c

def predict_heatwave(daily_data, hi_threshold=40, min_days=3):
    """
    Predict heatwave occurrence based on daily forecast data.
    A heatwave is defined as at least 'min_days' consecutive days with a heat index ≥ hi_threshold (°C).
    """
    heat_flags = []
    for day in daily_data:
        temp_max = day.get("temp", {}).get("max")
        humidity = day.get("humidity")
        if temp_max is None or humidity is None:
            heat_flags.append(False)
            continue
        hi = calculate_heat_index(temp_max, humidity)
        heat_flags.append(hi >= hi_threshold)
    
    best_streak = 0
    current_streak = 0
    best_start = None
    for i, flag in enumerate(heat_flags):
        if flag:
            if current_streak == 0:
                current_start = i
            current_streak += 1
            if current_streak > best_streak:
                best_streak = current_streak
                best_start = i - current_streak + 1
        else:
            current_streak = 0

    if best_streak >= min_days:
        start_date = daily_data[best_start]["dt"]
        end_date = daily_data[best_start + best_streak - 1]["dt"]
        return {"is_heatwave": True, "start_date": start_date, "end_date": end_date, "duration": best_streak}
    else:
        return {"is_heatwave": False, "message": "No heatwave predicted in the next 10 days."}

def generate_weekly_summary(daily_summaries):
    """
    Generate a simple weekly summary by counting heatwave and non-heatwave days.
    """
    try:
        heatwave_days = [d for d in daily_summaries if d.get("heatwave") == "Heatwave"]
        return {"heatwave_days": len(heatwave_days), "non_heatwave_days": len(daily_summaries) - len(heatwave_days)}
    except Exception as e:
        print("Error in generate_weekly_summary:", e)
        return {}

def generate_summaries(forecast_data):
    """
    Generate summaries from forecast data.
    Converts Unix timestamps to human-readable dates and adds a heatwave status for each day.
    Expects forecast_data["forecast"]["daily"] to be a list of daily forecast objects.
    """
    try:
        forecast = forecast_data.get("forecast", {})
        daily_data = forecast.get("daily", [])
        heatwave_pred = predict_heatwave(daily_data)
        daily_summaries = []
        for day in daily_data:
            date_ts = day.get("dt")
            date_str = datetime.fromtimestamp(date_ts).strftime("%Y-%m-%d") if date_ts else "N/A"
            hw_status = "Heatwave" if (heatwave_pred.get("is_heatwave") and date_ts >= heatwave_pred["start_date"] and date_ts <= heatwave_pred["end_date"]) else "No Heatwave"
            daily_summaries.append({
                "date": date_str,
                "min_temp": day.get("temp", {}).get("min"),
                "max_temp": day.get("temp", {}).get("max"),
                "humidity": day.get("humidity"),
                "weather": day.get("weather", [{}])[0].get("main", ""),
                "heatwave": hw_status,
                "dt": date_ts
            })
        weekly_summary = generate_weekly_summary(daily_summaries)
        return {"daily": daily_summaries, "weekly": weekly_summary, "heatwave": heatwave_pred}
    except Exception as e:
        print("Error in generate_summaries:", e)
        return {"daily": [], "weekly": {}, "heatwave": {}}
