from datetime import timedelta

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from outreach.models import ScheduledEvent

def public_home(request):
    today = timezone.localdate()

    events = list(
        ScheduledEvent.objects
        .filter(event_date__gte=today)
        .order_by("event_date", "start_time")[:9]
    )

    featured_event = events[0] if events else None
    upcoming_events = events[1:] if len(events) > 1 else []

    return render(
        request,
        "outreach/public_home.html",
        {
            "featured_event": featured_event,
            "upcoming_events": upcoming_events,
        },
    )