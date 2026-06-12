# code for pulling in hourly data from NWS for determination of whether a star party will be cancelled

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import re

import requests
from django.utils import timezone


NWS_HEADERS = {
    "User-Agent": "AAS Outreach Scheduler",
    "Accept": "application/geo+json",
}


def parse_nws_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def parse_valid_time(valid_time):
    start_text, duration_text = valid_time.split("/")
    start = parse_nws_time(start_text)

    hours = 0
    minutes = 0

    hour_match = re.search(r"(\d+)H", duration_text)
    minute_match = re.search(r"(\d+)M", duration_text)

    if hour_match:
        hours = int(hour_match.group(1))

    if minute_match:
        minutes = int(minute_match.group(1))

    return start, start + timedelta(hours=hours, minutes=minutes)


def get_grid_value(grid_property, event_datetime):
    if not grid_property:
        return None

    event_utc = event_datetime.astimezone(ZoneInfo("UTC"))

    for item in grid_property.get("values", []):
        start, end = parse_valid_time(item["validTime"])

        if start <= event_utc < end:
            return item.get("value")

    return None


def get_weather_text(weather_values, weather_type):
    if not weather_values:
        return ""

    matches = []

    for item in weather_values:
        item_weather = (item.get("weather") or "").lower()

        if weather_type not in item_weather:
            continue

        coverage = item.get("coverage") or ""
        intensity = item.get("intensity") or ""

        label_parts = []

        if coverage:
            label_parts.append(coverage.replace("_", " ").title())

        if intensity:
            label_parts.append(intensity.replace("_", " ").title())

        if not label_parts:
            label_parts.append(item.get("weather", "").replace("_", " ").title())

        matches.append(" ".join(label_parts))

    return "; ".join(matches)


def parse_wind_speed_mph(value):
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return round(float(value), 1)

    match = re.search(r"(\d+)", str(value))

    if not match:
        return None

    return round(float(match.group(1)), 1)


def get_nws_point_data(latitude, longitude):
    response = requests.get(
        f"https://api.weather.gov/points/{latitude},{longitude}",
        headers=NWS_HEADERS,
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def get_nws_alerts(latitude, longitude):
    response = requests.get(
        f"https://api.weather.gov/alerts/active?point={latitude},{longitude}",
        headers=NWS_HEADERS,
        timeout=20,
    )
    response.raise_for_status()

    data = response.json()

    watches = []
    warnings = []

    for feature in data.get("features", []):
        event_name = feature.get("properties", {}).get("event", "")

        if "Watch" in event_name:
            watches.append(event_name)

        if "Warning" in event_name:
            warnings.append(event_name)

    return {
        "watch_text": "; ".join(watches) if watches else "No current watches",
        "warning_text": "; ".join(warnings) if warnings else "No current warnings",
    }


def get_weather_for_event(event):
    if not event.partner.latitude or not event.partner.longitude:
        return None

    if not event.start_time:
        return None

    event_timezone = ZoneInfo(event.partner.timezone)

    event_datetime = datetime.combine(
        event.event_date,
        event.start_time,
        tzinfo=event_timezone,
    )

    point_data = get_nws_point_data(
        event.partner.latitude,
        event.partner.longitude,
    )

    grid_url = point_data["properties"]["forecastGridData"]

    grid_response = requests.get(
        grid_url,
        headers=NWS_HEADERS,
        timeout=20,
    )
    grid_response.raise_for_status()

    grid_data = grid_response.json()
    grid = grid_data["properties"]

    temperature_c = get_grid_value(grid.get("temperature"), event_datetime)
    heat_index_c = get_grid_value(grid.get("heatIndex"), event_datetime)
    wind_speed_kmh = get_grid_value(grid.get("windSpeed"), event_datetime)
    precip_probability = get_grid_value(
        grid.get("probabilityOfPrecipitation"),
        event_datetime,
    )
    sky_cover = get_grid_value(grid.get("skyCover"), event_datetime)
    weather_values = get_grid_value(grid.get("weather"), event_datetime)

    rain_text = get_weather_text(weather_values, "rain")
    thunder_text = get_weather_text(weather_values, "thunder")

    alerts = get_nws_alerts(
        event.partner.latitude,
        event.partner.longitude,
    )

    temperature_f = (
        round((temperature_c * 9 / 5) + 32, 1)
        if temperature_c is not None
        else None
    )

    heat_index_f = (
        round((heat_index_c * 9 / 5) + 32, 1)
        if heat_index_c is not None
        else None
    )

    wind_speed_mph = (
        round(wind_speed_kmh * 0.621371, 1)
        if wind_speed_kmh is not None
        else None
    )

    summary_parts = []

    if rain_text:
        summary_parts.append(f"Rain: {rain_text}")

    if thunder_text:
        summary_parts.append(f"Thunder: {thunder_text}")

    summary = "; ".join(summary_parts) or "No rain or thunder listed in NWS grid."

    return {
        "heat_index_f": heat_index_f,
        "temperature_f": temperature_f,
        "wind_speed_mph": wind_speed_mph,
        "precipitation_probability": precip_probability,
        "cloud_cover_percent": sky_cover,
        "rain_text": rain_text or "No rain listed",
        "thunder_text": thunder_text or "No thunder listed",
        "watch_text": alerts["watch_text"],
        "warning_text": alerts["warning_text"],
        "summary": summary,
        "last_checked": timezone.now(),
    }


def update_weather_for_event(event):
    try:
        forecast = get_weather_for_event(event)
    except Exception as error:
        event.weather_summary = f"Weather lookup failed: {error}"
        event.weather_watch_text = "Not checked"
        event.weather_warning_text = "Not checked"
        event.weather_last_checked = timezone.now()
        event.save()
        return False

    if forecast is None:
        event.weather_summary = "Forecast not available yet or no matching forecast."
        event.weather_watch_text = "Not checked"
        event.weather_warning_text = "Not checked"
        event.weather_last_checked = timezone.now()
        event.save()
        return False

    event.weather_heat_index_f = forecast.get("heat_index_f")
    event.weather_temperature_f = forecast.get("temperature_f")
    event.weather_wind_speed_mph = forecast.get("wind_speed_mph")
    event.weather_precipitation_probability = forecast.get(
        "precipitation_probability"
    )
    event.weather_cloud_cover_percent = forecast.get("cloud_cover_percent")
    event.weather_rain_text = forecast.get("rain_text") or "No rain listed"
    event.weather_thunder_text = forecast.get("thunder_text") or "No thunder listed"
    event.weather_watch_text = forecast.get("watch_text") or "No current watches"
    event.weather_warning_text = forecast.get("warning_text") or "No current warnings"
    event.weather_summary = forecast.get("summary") or "No forecast summary available"
    event.weather_last_checked = forecast.get("last_checked") or timezone.now()

    event.save()
    return True