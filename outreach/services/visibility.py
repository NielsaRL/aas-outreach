# code for determining if a celestial target from the seed_targets, and dynamic targets can be seen during the hours of the eventS

from datetime import datetime
from zoneinfo import ZoneInfo

from skyfield.api import Star, load, wgs84


def get_target_altitude_for_event(event, target):
    if target.ra_hours is None or target.dec_degrees is None:
        return None

    if not event.start_time:
        return None

    if not event.partner.latitude or not event.partner.longitude:
        return None

    timezone = ZoneInfo(event.partner.timezone)

    event_datetime = datetime.combine(
        event.event_date,
        event.start_time,
        tzinfo=timezone,
    )

    ts = load.timescale()
    t = ts.from_datetime(event_datetime)

    observer = wgs84.latlon(
        float(event.partner.latitude),
        float(event.partner.longitude),
    )

    eph = load("de421.bsp")
    observing_location = eph["earth"] + observer

    star = Star(
        ra_hours=float(target.ra_hours),
        dec_degrees=float(target.dec_degrees),
    )

    apparent = observing_location.at(t).observe(star).apparent()
    altitude, azimuth, distance = apparent.altaz()

    return {
        "altitude": round(altitude.degrees, 1),
        "azimuth": round(azimuth.degrees, 1),
    }


def target_is_visible_for_event(event, target, minimum_altitude=20):
    visibility = get_target_altitude_for_event(event, target)

    if visibility is None:
        return True  # allow discussion-only / no-coordinate targets through

    return visibility["altitude"] >= minimum_altitude

def get_target_visibility_window_for_event(event, target, minimum_altitude=20):
    if target.ra_hours is None or target.dec_degrees is None:
        return None

    if not event.start_time or not event.end_time:
        return None

    if not event.partner.latitude or not event.partner.longitude:
        return None

    timezone = ZoneInfo(event.partner.timezone)

    current_datetime = datetime.combine(
        event.event_date,
        event.start_time,
        tzinfo=timezone,
    )

    end_datetime = datetime.combine(
        event.event_date,
        event.end_time,
        tzinfo=timezone,
    )

    ts = load.timescale()
    eph = load("de421.bsp")

    observer = wgs84.latlon(
        float(event.partner.latitude),
        float(event.partner.longitude),
    )

    observing_location = eph["earth"] + observer

    star = Star(
        ra_hours=float(target.ra_hours),
        dec_degrees=float(target.dec_degrees),
    )

    visible_times = []
    best_altitude = None
    best_azimuth = None

    while current_datetime <= end_datetime:
        t = ts.from_datetime(current_datetime)

        apparent = observing_location.at(t).observe(star).apparent()
        altitude, azimuth, distance = apparent.altaz()

        if altitude.degrees >= minimum_altitude:
            visible_times.append(current_datetime)

            if best_altitude is None or altitude.degrees > best_altitude:
                best_altitude = altitude.degrees
                best_azimuth = azimuth.degrees

        current_datetime += timedelta(minutes=15)

    if not visible_times:
        return None

    return {
        "visible_start_time": visible_times[0].time(),
        "visible_end_time": visible_times[-1].time(),
        "altitude": round(best_altitude, 1),
        "azimuth": round(best_azimuth, 1),
    }