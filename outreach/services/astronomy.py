#code for calculating different types of dusk, suggested starting times, and moon illumination/phase

from datetime import datetime, timedelta
from math import cos, radians
from zoneinfo import ZoneInfo


from astral import LocationInfo
from astral.sun import sun, dusk
from skyfield.api import load, wgs84
from skyfield import almanac

def round_to_nearest_half_hour(dt):
    minute = dt.minute

    if minute < 15:
        return dt.replace(minute=0, second=0, microsecond=0)
    elif minute < 45:
        return dt.replace(minute=30, second=0, microsecond=0)
    else:
        return dt.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)


def calculate_twilight_times(event_date, latitude, longitude, timezone_name):
    tz = ZoneInfo(timezone_name)

    location = LocationInfo(
        name="Event Location",
        region="",
        timezone=timezone_name,
        latitude=latitude,
        longitude=longitude,
    )

    solar_times = sun(
        location.observer,
        date=event_date,
        tzinfo=tz,
    )

    sunset = solar_times["sunset"]

    civil_dusk = dusk(
        location.observer,
        date=event_date,
        depression=6,
        tzinfo=tz,
    )

    nautical_dusk = dusk(
        location.observer,
        date=event_date,
        depression=12,
        tzinfo=tz,
    )

    suggested_talk_start = round_to_nearest_half_hour(civil_dusk)
    suggested_laser_tour = round_to_nearest_half_hour(nautical_dusk)

    return {
        "sunset_time": sunset.time(),
        "civil_dusk_time": civil_dusk.time(),
        "nautical_dusk_time": nautical_dusk.time(),
        "suggested_talk_start_time": suggested_talk_start.time(),
        "suggested_laser_tour_time": suggested_laser_tour.time(),
    }

def calculate_moon_info(event_date, timezone_name):
    tz = ZoneInfo(timezone_name)

    ts = load.timescale()
    eph = load("de421.bsp")

    local_noon = datetime.combine(
        event_date,
        datetime.min.time().replace(hour=12),
        tzinfo=tz,
    )

    t = ts.from_datetime(local_noon)

    phase_degrees = almanac.moon_phase(eph, t).degrees

    if phase_degrees < 45:
        phase_name = "New Moon"
    elif phase_degrees < 90:
        phase_name = "Waxing Crescent"
    elif phase_degrees < 135:
        phase_name = "First Quarter"
    elif phase_degrees < 180:
        phase_name = "Waxing Gibbous"
    elif phase_degrees < 225:
        phase_name = "Full Moon"
    elif phase_degrees < 270:
        phase_name = "Waning Gibbous"
    elif phase_degrees < 315:
        phase_name = "Last Quarter"
    else:
        phase_name = "Waning Crescent"

    illumination = (1 - cos(radians(phase_degrees))) / 2 * 100

    return {
        "moon_phase": phase_name,
        "moon_illumination": round(illumination, 1),
    }


def calculate_moonrise(event_date, latitude, longitude, timezone_name):
    """
    Calculate the first moonrise occurring on the specified local date.

    Args:
        event_date: Python date object.
        latitude: Observer latitude in decimal degrees.
        longitude: Observer longitude in decimal degrees.
        timezone_name: IANA timezone, e.g. "America/Chicago".

    Returns:
        A timezone-aware datetime representing local moonrise,
        or None if no moonrise occurs on that date.
    """
    if latitude is None or longitude is None:
        return None

    tz = ZoneInfo(timezone_name)
    ts = load.timescale()
    eph = load("de421.bsp")

    # Define the start and end of the local calendar day.
    local_start = datetime.combine(
        event_date,
        datetime.min.time(),
        tzinfo=tz,
    )

    local_end = datetime.combine(
        event_date + timedelta(days=1),
        datetime.min.time(),
        tzinfo=tz,
    )

    # Construct the observer's geographic location.
    observer = wgs84.latlon(
        latitude_degrees=latitude,
        longitude_degrees=longitude,
    )

    # Skyfield expects a geographic observer, Moon target,
    # start time, and end time.
    times, valid = almanac.find_risings(
        eph["earth"] + observer,
        eph["moon"],
        ts.from_datetime(local_start),
        ts.from_datetime(local_end),
    )

    # Find the first valid moonrise on the requested local date.
    for time, is_valid in zip(times, valid):
        if is_valid:
            local_rise = time.utc_datetime().astimezone(tz)

            if local_rise.date() == event_date:
                return local_rise

    # No moonrise occurred during this local calendar day.
    return None
