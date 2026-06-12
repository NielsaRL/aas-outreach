#code for pulling in information on dynamic celestial targets

from datetime import datetime
from zoneinfo import ZoneInfo

from skyfield.api import load, wgs84


DYNAMIC_TARGETS = [
    ("moon", "Moon", "MOON"),
    ("mercury", "Mercury", "PLANET"),
    ("venus", "Venus", "PLANET"),
    ("mars", "Mars", "PLANET"),
    ("jupiter barycenter", "Jupiter", "PLANET"),
    ("saturn barycenter", "Saturn", "PLANET"),
]


def get_visible_solar_system_targets(event):
    if not event.partner.latitude or not event.partner.longitude:
        return []

    if not event.start_time:
        return []

    timezone = ZoneInfo(event.partner.timezone)

    event_datetime = datetime.combine(
        event.event_date,
        event.start_time,
        tzinfo=timezone,
    )

    ts = load.timescale()
    eph = load("de421.bsp")

    observer = wgs84.latlon(
        float(event.partner.latitude),
        float(event.partner.longitude),
    )

    observing_location = eph["earth"] + observer
    t = ts.from_datetime(event_datetime)

    visible_targets = []

    for skyfield_name, display_name, target_type in DYNAMIC_TARGETS:
        body = eph[skyfield_name]

        apparent = observing_location.at(t).observe(body).apparent()
        altitude, azimuth, distance = apparent.altaz()

        if altitude.degrees >= 15:
            visible_targets.append({
                "name": display_name,
                "target_type": target_type,
                "altitude": round(altitude.degrees, 1),
                "azimuth": round(azimuth.degrees, 1),
                "notes": (
                    f"{display_name} should be visible near event start, "
                    f"about {round(altitude.degrees, 1)}° above the horizon."
                ),
            })

    return visible_targets