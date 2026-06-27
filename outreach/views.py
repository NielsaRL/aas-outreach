from datetime import timedelta

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import get_object_or_404

from .forms import VolunteerRegistrationForm
from .models import ScheduledEvent, EventVolunteer


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

def register(request):
    if request.method == "POST":
        form = VolunteerRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("volunteer_portal")
    else:
        form = VolunteerRegistrationForm()

    return render(request, "outreach/register.html", {"form": form})


@login_required
def volunteer_portal(request):
    today = timezone.localdate()
    one_year_from_today = today + timedelta(days=365)

    events = (
        ScheduledEvent.objects
        .filter(event_date__gte=today, event_date__lte=one_year_from_today)
        .order_by("event_date", "start_time")
    )

    volunteer = getattr(request.user, "volunteer_profile", None)

    return render(request, "outreach/volunteer_portal.html", {
        "events": events,
        "volunteer": volunteer,
    })

@login_required
def volunteer_for_event(request, event_id):
    event = get_object_or_404(ScheduledEvent, id=event_id)
    volunteer = request.user.volunteer_profile

    EventVolunteer.objects.get_or_create(
        event=event,
        volunteer=volunteer,
    )

    messages.success(request, f"You are signed up for {event.event_name}.")
    return redirect("volunteer_portal")