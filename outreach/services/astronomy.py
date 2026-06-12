#code for calculating different types of dusk, suggested starting times, and moon illumination/phase

from datetime import datetime, timedelta
from math import cos, radians
from zoneinfo import ZoneInfo


from astral import LocationInfo
from astral.sun import sun, dusk
from skyfield.api import load
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