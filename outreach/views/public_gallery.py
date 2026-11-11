
from datetime import datetime, timedelta

from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_exempt

from outreach.models import ScheduledEvent


@xframe_options_exempt
def public_event_gallery(request):
    """Display manually published events that have not yet ended."""

    now = timezone.localtime()
    today = now.date()

    events = (
        ScheduledEvent.objects
        .filter(
            show_on_public_website=True,
            event_date__gte=today - timedelta(days=1),
        )
        .select_related("partner")
        .order_by("event_date", "start_time")
    )

    visible_events = []

    for event in events:
        if event.end_time:
            end_datetime = datetime.combine(event.event_date, event.end_time)

            # Handle events that finish after midnight.
            if event.start_time and event.end_time < event.start_time:
                end_datetime += timedelta(days=1)

            end_datetime = timezone.make_aware(
                end_datetime,
                timezone.get_current_timezone(),
            )

            if end_datetime <= now:
                continue
        elif event.event_date < today:
            continue

        visible_events.append(event)

    response = render(
        request,
        "outreach/public_event_gallery.html",
        {"events": visible_events},
    )

    response["Content-Security-Policy"] = (
        "frame-ancestors 'self' https://austinastro.org"
    )

    return response
