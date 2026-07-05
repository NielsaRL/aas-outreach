from datetime import timedelta

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone
from django.contrib import messages

from outreach.models import EventVolunteer, ScheduledEvent, Volunteer
from outreach.forms import VolunteerProfileForm, VolunteerRegistrationForm

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

    volunteer = getattr(request.user, "volunteer_profile", None)

    events = (
        ScheduledEvent.objects
        .filter(event_date__gte=today, event_date__lte=one_year_from_today)
        .order_by("event_date", "start_time")
    )

    signed_up_event_ids = set()

    if volunteer:
        signed_up_event_ids = set(
            EventVolunteer.objects.filter(
                volunteer=volunteer
            ).values_list("event_id", flat=True)
        )

    my_events = events.filter(id__in=signed_up_event_ids)
    available_events = events.exclude(id__in=signed_up_event_ids)

    return render(
        request,
        "outreach/volunteer_portal.html",
        {
            "volunteer": volunteer,
            "my_events": my_events,
            "available_events": available_events,
            "signed_up_event_ids": signed_up_event_ids,
        },
    )

@login_required
def volunteer_for_event(request, event_id):
    event = get_object_or_404(ScheduledEvent, id=event_id)
    volunteer = getattr(request.user, "volunteer_profile", None)

    if volunteer is None:
        volunteer = Volunteer.objects.create(
            user=request.user,
            first_name=request.user.first_name or request.user.username,
            last_name=request.user.last_name or "",
            email=request.user.email or "",
            active=True,
        )

    EventVolunteer.objects.get_or_create(
        event=event,
        volunteer=volunteer,
    )

    messages.success(request, f"You are signed up for {event.event_name}.")
    return redirect("volunteer_portal")


@login_required
def cancel_volunteer_for_event(request, event_id):
    event = get_object_or_404(ScheduledEvent, id=event_id)
    volunteer = getattr(request.user, "volunteer_profile", None)

    if volunteer:
        EventVolunteer.objects.filter(
            event=event,
            volunteer=volunteer,
        ).delete()

        messages.success(request, f"You are no longer signed up for {event.event_name}.")

    return redirect("volunteer_portal")

@login_required
def volunteer_event_detail(request, event_id):
    event = get_object_or_404(ScheduledEvent, id=event_id)
    volunteer = getattr(request.user, "volunteer_profile", None)

    is_signed_up = False
    if volunteer:
        is_signed_up = EventVolunteer.objects.filter(
            event=event,
            volunteer=volunteer,
        ).exists()

    event_volunteers = EventVolunteer.objects.filter(
        event=event
    ).select_related("volunteer")

    event_targets = event.event_targets.select_related("target").all()

    return render(
        request,
        "outreach/volunteer_event_detail.html",
        {
            "event": event,
            "volunteer": volunteer,
            "is_signed_up": is_signed_up,
            "event_volunteers": event_volunteers,
            "event_targets": event_targets,
        },
    )

@login_required
def edit_volunteer_profile(request):
    volunteer = getattr(request.user, "volunteer_profile", None)

    if volunteer is None:
        volunteer = Volunteer.objects.create(
            user=request.user,
            first_name=request.user.first_name or request.user.username,
            last_name=request.user.last_name or "",
            email=request.user.email or "",
            active=True,
        )

    if request.method == "POST":
        form = VolunteerProfileForm(request.POST, instance=volunteer)

        if form.is_valid():
            volunteer = form.save()

            request.user.first_name = volunteer.first_name
            request.user.last_name = volunteer.last_name
            request.user.email = volunteer.email
            request.user.save()

            messages.success(request, "Your volunteer profile has been updated.")
            return redirect("volunteer_portal")
    else:
        form = VolunteerProfileForm(instance=volunteer)

    return render(
        request,
        "outreach/edit_volunteer_profile.html",
        {
            "form": form,
            "volunteer": volunteer,
        },
    )