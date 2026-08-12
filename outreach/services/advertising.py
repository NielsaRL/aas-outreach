import json
import math

from dataclasses import dataclass
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Optional

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from outreach.models import (
    AdvertisingCampaign,
    AdvertisingOutlet,
    EventAdvertisement,
    ScheduledEvent,
)


CITY_LOOKUP_FILE = (
    Path(settings.BASE_DIR)
    / "outreach"
    / "data"
    / "texas_city_centers.json"
)


@dataclass
class CampaignGenerationResult:
    campaign: AdvertisingCampaign
    campaign_created: bool
    advertisements_created: int
    advertisements_existing: int
    outlets_skipped_deadline: int
    outlets_skipped_radius: int
    outlets_skipped_missing_city: int
    outlets_skipped_event_type: int
    outlets_skipped_missing_venue_coordinates: int


def normalize_location_name(value: str) -> str:
    """
    Normalize a city or state value for city-center lookup.
    """

    return " ".join((value or "").strip().lower().split())


def build_city_lookup_key(city: str, state: str) -> str:
    """
    Build the normalized city lookup key used by the JSON file.
    """

    normalized_city = normalize_location_name(city)
    normalized_state = normalize_location_name(state or "Texas")

    return f"{normalized_city}|{normalized_state}"


@lru_cache(maxsize=1)
def load_city_centers() -> dict:
    """
    Load and cache city-center coordinates.

    The JSON file is read only once per Django process.
    """

    if not CITY_LOOKUP_FILE.exists():
        return {}

    try:
        with CITY_LOOKUP_FILE.open(
            mode="r",
            encoding="utf-8",
        ) as city_file:
            data = json.load(city_file)
    except (OSError, json.JSONDecodeError):
        return {}

    if not isinstance(data, dict):
        return {}

    return data


def get_city_center(
    city: str,
    state: str,
) -> Optional[tuple[float, float]]:
    """
    Return the city-center latitude and longitude for an outlet.
    """

    if not city:
        return None

    lookup_key = build_city_lookup_key(
        city=city,
        state=state,
    )

    city_data = load_city_centers().get(lookup_key)

    if not isinstance(city_data, dict):
        return None

    latitude = city_data.get("latitude")
    longitude = city_data.get("longitude")

    if latitude is None or longitude is None:
        return None

    try:
        return float(latitude), float(longitude)
    except (TypeError, ValueError):
        return None


def get_numeric_attribute(
    obj,
    possible_names: tuple[str, ...],
) -> Optional[float]:
    """
    Find and convert the first populated coordinate attribute.

    This supports slightly different coordinate field names without
    requiring the advertising service to know exactly which one is used.
    """

    if obj is None:
        return None

    for field_name in possible_names:
        value = getattr(obj, field_name, None)

        if value in (None, ""):
            continue

        try:
            return float(value)
        except (TypeError, ValueError):
            continue

    return None


def get_event_coordinates(
    event: ScheduledEvent,
) -> Optional[tuple[float, float]]:
    """
    Return venue coordinates from the event or its partner.

    Add or remove candidate field names here if your models use a
    different naming convention.
    """

    coordinate_sources = [
        event,
        getattr(event, "partner", None),
    ]

    latitude_field_names = (
        "latitude",
        "lat",
        "location_latitude",
        "venue_latitude",
    )

    longitude_field_names = (
        "longitude",
        "lon",
        "lng",
        "location_longitude",
        "venue_longitude",
    )

    for source in coordinate_sources:
        latitude = get_numeric_attribute(
            source,
            latitude_field_names,
        )

        longitude = get_numeric_attribute(
            source,
            longitude_field_names,
        )

        if latitude is not None and longitude is not None:
            return latitude, longitude

    return None


def calculate_distance_miles(
    latitude_1: float,
    longitude_1: float,
    latitude_2: float,
    longitude_2: float,
) -> float:
    """
    Calculate straight-line distance using the Haversine formula.
    """

    earth_radius_miles = 3958.7613

    lat_1_radians = math.radians(latitude_1)
    lat_2_radians = math.radians(latitude_2)

    latitude_difference = math.radians(
        latitude_2 - latitude_1
    )

    longitude_difference = math.radians(
        longitude_2 - longitude_1
    )

    haversine_value = (
        math.sin(latitude_difference / 2) ** 2
        + math.cos(lat_1_radians)
        * math.cos(lat_2_radians)
        * math.sin(longitude_difference / 2) ** 2
    )

    central_angle = 2 * math.atan2(
        math.sqrt(haversine_value),
        math.sqrt(1 - haversine_value),
    )

    return earth_radius_miles * central_angle


def outlet_accepts_event(
    outlet: AdvertisingOutlet,
    event: ScheduledEvent,
) -> bool:
    """
    Return True when the outlet accepts the event type.
    """

    event_type_rules = {
        "STAR_PARTY": outlet.accepts_star_parties,
        "SOLAR_OUTREACH": outlet.accepts_solar_outreach,
        "LIBRARY_PROGRAM": outlet.accepts_library_programs,
        "SIDEWALK_ASTRONOMY": (
            outlet.accepts_sidewalk_astronomy
        ),
        "CUSTOM": outlet.accepts_custom_events,
    }

    return event_type_rules.get(
        event.event_title_type,
        False,
    )


def calculate_submission_deadline(
    outlet: AdvertisingOutlet,
    event: ScheduledEvent,
) -> date:
    """
    Calculate the last acceptable submission date.
    """

    return event.event_date - timedelta(
        days=outlet.minimum_lead_days
    )


def outlet_is_within_campaign_area(
    outlet: AdvertisingOutlet,
    event: ScheduledEvent,
    event_coordinates: Optional[tuple[float, float]],
) -> tuple[bool, str, Optional[float]]:
    """
    Decide whether an outlet is geographically applicable.
    """

    if event.advertise_to_full_service_area:
        return True, "event_full_service_area", None

    if outlet.covers_full_service_area:
        return True, "outlet_full_service_area", None

    if event_coordinates is None:
        return False, "missing_venue_coordinates", None

    city_coordinates = get_city_center(
        city=outlet.city,
        state=outlet.state,
    )

    if city_coordinates is None:
        return False, "missing_city", None

    event_latitude, event_longitude = event_coordinates
    city_latitude, city_longitude = city_coordinates

    distance_miles = calculate_distance_miles(
        latitude_1=event_latitude,
        longitude_1=event_longitude,
        latitude_2=city_latitude,
        longitude_2=city_longitude,
    )

    included = distance_miles <= event.advertising_radius_miles

    if included:
        return True, "within_radius", distance_miles

    return False, "outside_radius", distance_miles

@transaction.atomic
def generate_advertising_campaign(
    event: ScheduledEvent,
    generated_by=None,
) -> CampaignGenerationResult:
    """
    Generate or safely update an advertising campaign.

    Existing tasks are preserved. Regeneration only adds newly applicable
    outlets. Outlets whose deadlines have passed are skipped.
    """

    campaign, campaign_created = (
        AdvertisingCampaign.objects.get_or_create(
            event=event,
            defaults={
                "status": AdvertisingCampaign.Status.ACTIVE,
                "generated_by": generated_by,
            },
        )
    )

    if not campaign_created:
        campaign.last_regenerated_at = timezone.now()

        if campaign.status in {
            AdvertisingCampaign.Status.DRAFT,
            AdvertisingCampaign.Status.COMPLETE,
        }:
            campaign.status = AdvertisingCampaign.Status.ACTIVE

        campaign.save(
            update_fields=[
                "last_regenerated_at",
                "status",
            ]
        )

    event_coordinates = get_event_coordinates(event)
    today = timezone.localdate()

    created_count = 0
    existing_count = 0
    skipped_deadline_count = 0
    skipped_radius_count = 0
    skipped_missing_city_count = 0
    skipped_event_type_count = 0
    skipped_missing_venue_coordinates_count = 0

    outlets = AdvertisingOutlet.objects.filter(
        active=True,
    ).order_by(
        "priority",
        "estimated_submission_minutes",
        "name",
    )

    for outlet in outlets:
        if not outlet_accepts_event(outlet, event):
            skipped_event_type_count += 1
            continue

        submission_deadline = calculate_submission_deadline(
            outlet=outlet,
            event=event,
        )

        if submission_deadline < today:
            skipped_deadline_count += 1
            continue

        include_outlet, reason, distance_miles = (
            outlet_is_within_campaign_area(
                outlet=outlet,
                event=event,
                event_coordinates=event_coordinates,
            )
        )

        if not include_outlet:
            if reason == "outside_radius":
                skipped_radius_count += 1
            elif reason == "missing_city":
                skipped_missing_city_count += 1
            elif reason == "missing_venue_coordinates":
                skipped_missing_venue_coordinates_count += 1

            continue

        advertisement, advertisement_created = (
            EventAdvertisement.objects.get_or_create(
                campaign=campaign,
                outlet=outlet,
                defaults={
                    "status": (
                        EventAdvertisement.Status.NOT_STARTED
                    ),
                    "submission_deadline": submission_deadline,
                },
            )
        )

        if advertisement_created:
            created_count += 1
        else:
            existing_count += 1

    return CampaignGenerationResult(
        campaign=campaign,
        campaign_created=campaign_created,
        advertisements_created=created_count,
        advertisements_existing=existing_count,
        outlets_skipped_deadline=skipped_deadline_count,
        outlets_skipped_radius=skipped_radius_count,
        outlets_skipped_missing_city=skipped_missing_city_count,
        outlets_skipped_event_type=skipped_event_type_count,
        outlets_skipped_missing_venue_coordinates=(
            skipped_missing_venue_coordinates_count
        ),
    )