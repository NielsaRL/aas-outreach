from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

import calendar
from datetime import date, timedelta

from outreach.services.astronomy import calculate_moon_info

from outreach.forms import (EventVolunteerSignupForm, VolunteerProfileForm, VolunteerRegistrationForm,)
from outreach.models import EventVolunteer, ScheduledEvent, Volunteer


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

    upcoming_events = (
        ScheduledEvent.objects
        .filter(
            event_date__gte=today,
            event_date__lte=one_year_from_today,
        )
        .order_by("event_date", "start_time")
    )

    signed_up_event_ids = set()
    previous_events = ScheduledEvent.objects.none()

    if volunteer:
        signed_up_event_ids = set(
            EventVolunteer.objects.filter(
                volunteer=volunteer
            ).values_list("event_id", flat=True)
        )

        previous_events = (
            ScheduledEvent.objects
            .filter(
                id__in=signed_up_event_ids,
                event_date__lt=today,
            )
            .order_by("-event_date", "-start_time")
        )

    my_events = upcoming_events.filter(
        id__in=signed_up_event_ids
    )

    available_events = upcoming_events.exclude(
        id__in=signed_up_event_ids
    )

    return render(
        request,
        "outreach/volunteer_portal.html",
        {
            "volunteer": volunteer,
            "my_events": my_events,
            "available_events": available_events,
            "previous_events": previous_events,
            "signed_up_event_ids": signed_up_event_ids,
        },
    )

@login_required
def volunteer_calendar(request):
    today = timezone.localdate()

    try:
        year = int(request.GET.get("year", today.year))
        month = int(request.GET.get("month", today.month))
    except (TypeError, ValueError):
        year = today.year
        month = today.month

    if month < 1 or month > 12:
        year = today.year
        month = today.month

    first_day = date(year, month, 1)
    last_day = date(
        year,
        month,
        calendar.monthrange(year, month)[1],
    )

    events = (
        ScheduledEvent.objects
        .filter(
            event_date__gte=first_day,
            event_date__lte=last_day,
        )
        .exclude(status="CANCELLED")
        .select_related("partner")
        .order_by("event_date", "start_time")
    )

    events_by_date = {}

    for event in events:
        events_by_date.setdefault(
            event.event_date,
            [],
        ).append(event)

    cal = calendar.Calendar(firstweekday=6)
    raw_weeks = cal.monthdatescalendar(year, month)

    weeks = []

    for raw_week in raw_weeks:
        week = []

        for day_date in raw_week:
            moon_data = calculate_moon_info(
                event_date=day_date,
                timezone_name="America/Chicago",
            )

            illumination = moon_data.get("moon_illumination") or 0
            phase = moon_data.get("moon_phase", "")

            if illumination < 12:
                moon_icon = "🌑"
            elif illumination < 37:
                moon_icon = "🌒"
            elif illumination < 62:
                moon_icon = "🌓"
            elif illumination < 87:
                moon_icon = "🌔"
            else:
                moon_icon = "🌕"

            week.append(
                {
                    "date": day_date,
                    "day": day_date.day,
                    "in_current_month": day_date.month == month,
                    "is_today": day_date == today,
                    "events": events_by_date.get(day_date, []),
                    "moon_phase": phase,
                    "moon_illumination": illumination,
                    "moon_color": (
                        round(65 + ((illumination / 100) * 175)),
                        round(67 + ((illumination / 100) * 175)),
                        round(130 + ((illumination / 100) * 125)),
                    ),
                    "moon_icon": moon_icon,
                }
            )

        weeks.append(week)

    previous_month = month - 1
    previous_year = year

    if previous_month == 0:
        previous_month = 12
        previous_year -= 1

    next_month = month + 1
    next_year = year

    if next_month == 13:
        next_month = 1
        next_year += 1

    return render(
        request,
        "outreach/volunteer_calendar.html",
        {
            "weeks": weeks,
            "month": month,
            "year": year,
            "month_name": calendar.month_name[month],
            "previous_month": previous_month,
            "previous_year": previous_year,
            "next_month": next_month,
            "next_year": next_year,
        },
    )

@login_required
def volunteer_for_event(request, event_id):
    if request.method != "POST":
        return redirect("volunteer_event_detail", event_id=event_id)

    volunteer = getattr(request.user, "volunteer_profile", None)

    if volunteer is None:
        volunteer = Volunteer.objects.create(
            user=request.user,
            first_name=request.user.first_name or request.user.username,
            last_name=request.user.last_name or "",
            email=request.user.email or "",
            active=True,
        )

    existing_signup = EventVolunteer.objects.filter(
        event_id=event_id,
        volunteer=volunteer,
    ).first()

    if existing_signup:
        messages.info(
            request,
            "You are already signed up for this event.",
        )
        return redirect("volunteer_event_detail", event_id=event_id)

    form = EventVolunteerSignupForm(request.POST)

    if not form.is_valid():
        event = get_object_or_404(ScheduledEvent, id=event_id)

        event_volunteers = (
            EventVolunteer.objects
            .filter(event=event)
            .select_related("volunteer")
        )

        event_targets = event.event_targets.select_related("target").all()

        return render(
            request,
            "outreach/volunteer_event_detail.html",
            {
                "event": event,
                "volunteer": volunteer,
                "is_signed_up": False,
                "event_volunteers": event_volunteers,
                "event_targets": event_targets,
                "signup_form": form,
            },
        )

    with transaction.atomic():
        event = (
            ScheduledEvent.objects
            .select_for_update()
            .get(id=event_id)
        )

        current_volunteer_count = EventVolunteer.objects.filter(
            event=event
        ).count()

        if (
            event.volunteer_capacity is not None
            and current_volunteer_count >= event.volunteer_capacity
        ):
            messages.error(
                request,
                "This event has reached its volunteer capacity.",
            )
            return redirect(
                "volunteer_event_detail",
                event_id=event.id,
            )

        signup = form.save(commit=False)
        signup.event = event
        signup.volunteer = volunteer
        signup.full_clean()
        signup.save()

    messages.success(
        request,
        f"You are signed up for {event.event_name}.",
    )

    return redirect(
        "volunteer_event_detail",
        event_id=event.id,
    )


@login_required
def cancel_volunteer_for_event(request, event_id):
    event = get_object_or_404(ScheduledEvent, id=event_id)
    volunteer = getattr(request.user, "volunteer_profile", None)

    if volunteer:
        EventVolunteer.objects.filter(
            event=event,
            volunteer=volunteer,
        ).delete()

        messages.success(
            request,
            f"You are no longer signed up for {event.event_name}.",
        )

    return redirect("volunteer_portal")


@login_required
def volunteer_event_detail(request, event_id):
    event = get_object_or_404(ScheduledEvent, id=event_id)
    volunteer = getattr(request.user, "volunteer_profile", None)

    signup = None

    if volunteer:
        signup = EventVolunteer.objects.filter(
            event=event,
            volunteer=volunteer,
        ).first()

    is_signed_up = signup is not None

    event_volunteers = (
        EventVolunteer.objects
        .filter(event=event)
        .select_related("volunteer")
    )

    event_targets = event.event_targets.select_related("target").all()

    location_resources = []

    if event.partner:
        location_resources = event.partner.location_resources.filter(
            active=True
        )

    signup_form = None

    if not is_signed_up and not event.volunteer_signup_full:
        signup_form = EventVolunteerSignupForm()

    return render(
        request,
        "outreach/volunteer_event_detail.html",
        {
            "event": event,
            "volunteer": volunteer,
            "is_signed_up": is_signed_up,
            "signup": signup,
            "signup_form": signup_form,
            "event_volunteers": event_volunteers,
            "event_targets": event_targets,
            "location_resources": location_resources,
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
        form = VolunteerProfileForm(
            request.POST,
            instance=volunteer,
        )

        if form.is_valid():
            volunteer = form.save()

            request.user.first_name = volunteer.first_name
            request.user.last_name = volunteer.last_name
            request.user.email = volunteer.email
            request.user.save()

            messages.success(
                request,
                "Your volunteer profile has been updated.",
            )

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