from __future__ import annotations

from datetime import date, datetime, time
from typing import Any

from django.utils import timezone

from outreach.models import AdvertisingCampaign


class SafeFormatDict(dict):
    """
    Leaves unknown placeholders unchanged instead of raising KeyError.

    Example:
        "{event_name} - {unknown}".format_map(...)
        becomes:
        "Star Party - {unknown}"
    """

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"

def _format_date(value: Any) -> str:
    if not value:
        return ""

    if isinstance(value, datetime):
        value = timezone.localtime(value).date()

    if isinstance(value, date):
        return value.strftime("%A, %B %d, %Y").replace(" 0", " ")

    return str(value)


def _format_time(value: Any) -> str:
    if not value:
        return ""

    if isinstance(value, datetime):
        value = timezone.localtime(value).time()

    if isinstance(value, time):
        formatted = value.strftime("%I:%M %p").lstrip("0")
        return formatted.replace(":00 ", " ")

    return str(value)

def _get_event_name(event) -> str:
    """
    Returns the best available event name without depending on one exact
    ScheduledEvent field name.
    """

    for field_name in ("name", "title", "event_name"):
        value = getattr(event, field_name, None)

        if value:
            return str(value)

    return str(event)


def _get_location(event):
    """
    Returns the best available location/venue object.
    """

    for field_name in ("location", "venue", "partner"):
        value = getattr(event, field_name, None)

        if value:
            return value

    return None


def _get_partner(event):
    return getattr(event, "partner", None)


def _get_first_value(obj, field_names: tuple[str, ...], default: str = "") -> str:
    if obj is None:
        return default

    for field_name in field_names:
        value = getattr(obj, field_name, None)

        if value not in (None, ""):
            return str(value)

    return default


def build_advertising_context(campaign: AdvertisingCampaign) -> dict[str, str]:
    """
    Builds the placeholder values available to playbook templates.
    """

    event = campaign.event
    location = _get_location(event)
    partner = _get_partner(event)

    event_date = (
        getattr(event, "event_date", None)
        or getattr(event, "date", None)
        or getattr(event, "start_date", None)
        or getattr(event, "start_datetime", None)
        or getattr(event, "start_time", None)
    )

    start_time = (
        getattr(event, "start_time", None)
        or getattr(event, "start_datetime", None)
    )

    end_time = (
        getattr(event, "end_time", None)
        or getattr(event, "end_datetime", None)
    )

    location_name = _get_first_value(
        location,
        (
            "name",
            "location_name",
            "venue_name",
            "title",
        ),
    )

    partner_name = _get_first_value(
        partner,
        (
            "name",
            "organization_name",
            "title",
        ),
    )

    city = (
        _get_first_value(location, ("city",))
        or _get_first_value(partner, ("city",))
    )

    address = (
        _get_first_value(
            location,
            (
                "address",
                "street_address",
                "address_line_1",
            ),
        )
        or _get_first_value(
            partner,
            (
                "address",
                "street_address",
                "address_line_1",
            ),
        )
    )

    event_type = getattr(event, "event_type", "")

    if hasattr(event, "get_event_type_display"):
        event_type = event.get_event_type_display()

    return {
        "event_name": _get_event_name(event),
        "event_date": _format_date(event_date),
        "start_time": _format_time(start_time),
        "end_time": _format_time(end_time),
        "location_name": location_name,
        "partner_name": partner_name,
        "city": city,
        "address": address,
        "event_type": str(event_type or ""),
    }


def render_advertising_template(
    template: str,
    context: dict[str, str],
) -> str:
    """
    Replaces playbook placeholders with event values.
    """

    if not template:
        return ""

    return template.format_map(SafeFormatDict(context)).strip()


def generate_campaign_copy(
    campaign: AdvertisingCampaign,
    *,
    overwrite_existing: bool = False,
) -> AdvertisingCampaign:
    """
    Generates and saves advertising copy for one campaign.

    Existing campaign copy is preserved unless overwrite_existing=True.
    """

    playbook = campaign.playbook

    if playbook is None:
        raise ValueError(
            "A playbook must be selected before advertising copy can be generated."
        )

    if not playbook.active:
        raise ValueError(
            f'The advertising playbook "{playbook}" is inactive.'
        )

    context = build_advertising_context(campaign)

    generated_values = {
        "short_description": render_advertising_template(
            playbook.short_description_template,
            context,
        ),
        "long_description": render_advertising_template(
            playbook.long_description_template,
            context,
        ),
        "facebook_copy": (
            render_advertising_template(
                playbook.facebook_template,
                context,
            )
            if playbook.generate_facebook_copy
            else ""
        ),
        "newsletter_copy": (
            render_advertising_template(
                playbook.newsletter_template,
                context,
            )
            if playbook.generate_newsletter_copy
            else ""
        ),
        "community_calendar_copy": (
            render_advertising_template(
                playbook.community_calendar_template,
                context,
            )
            if playbook.generate_calendar_copy
            else ""
        ),
        "email_copy": (
            render_advertising_template(
                playbook.email_template,
                context,
            )
            if playbook.generate_email_copy
            else ""
        ),
        "image_guidance": playbook.image_guidance.strip(),
    }

    changed_fields: list[str] = []

    for field_name, generated_value in generated_values.items():
        existing_value = getattr(campaign, field_name, "")

        if overwrite_existing or not existing_value:
            setattr(campaign, field_name, generated_value)
            changed_fields.append(field_name)

    campaign.copy_generated_at = timezone.now()
    changed_fields.append("copy_generated_at")

    campaign.save(update_fields=changed_fields)

    return campaign