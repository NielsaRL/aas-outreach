##scheduler logic based on varaibles entered for each venue. This is aimed at automating the yearly schedule for recurrent partners. One offs are added manually.


from datetime import datetime, timedelta
from outreach.models import Partner, SuggestedEvent
from outreach.services.astronomy import calculate_moon_info
from outreach.services.astronomy import calculate_twilight_times, round_to_nearest_half_hour
import holidays
from collections import defaultdict


SCHEDULING_TYPE_WEIGHT = {
    "DARKEST": 300,
    "REQUESTS_MOON": 200,
    "NO_PREFERENCE": 100,
    "CUSTOM": 50,
}


def get_weekday_occurrence_in_month(event_date):
    return ((event_date.day - 1) // 7) + 1


def is_last_weekday_of_month(event_date):
    next_week = event_date + timedelta(days=7)
    return next_week.month != event_date.month


def partner_allows_calendar_date(partner, event_date):
    allowed_months = [int(m) for m in partner.allowed_months]
    allowed_weekdays = [int(d) for d in partner.allowed_weekdays]
    allowed_occurrences = list(partner.allowed_weekday_occurrences)

    if allowed_months and event_date.month not in allowed_months:
        return False

    if allowed_weekdays and event_date.weekday() not in allowed_weekdays:
        return False

    if allowed_occurrences:
        occurrence = str(get_weekday_occurrence_in_month(event_date))

        if occurrence in allowed_occurrences:
            return True

        if "LAST" in allowed_occurrences and is_last_weekday_of_month(event_date):
            return True

        return False

    return True

def date_is_in_holiday_week(event_date):
    us_holidays = holidays.US(years=event_date.year)

    week_start = event_date - timedelta(days=event_date.weekday())
    week_end = week_start + timedelta(days=6)

    for holiday_date in us_holidays:
        if week_start <= holiday_date <= week_end:
            return True

    return False

def partner_allows_moon(partner, event_date):
    moon_data = calculate_moon_info(
        event_date=event_date,
        timezone_name=partner.timezone,
    )

    illumination = moon_data["moon_illumination"]

    if partner.scheduling_type == "DARKEST":
        return illumination <= 25

    if partner.scheduling_type == "REQUESTS_MOON":
        return 25 <= illumination <= 85

    return True


def partner_date_was_rejected(partner, event_date):
    return SuggestedEvent.objects.filter(
        partner=partner,
        suggested_date=event_date,
        status="REJECTED",
    ).exists()


def partner_already_has_active_suggestion(partner):
    return SuggestedEvent.objects.filter(
        partner=partner,
        status__in=["SUGGESTED", "APPROVED"],
    ).count()


def generate_partner_candidate_dates(partner, start_date, end_date):
    candidate_dates = []
    current_date = start_date

    while current_date <= end_date:
        if partner_date_was_rejected(partner, current_date):
            current_date += timedelta(days=1)
            continue
        if date_is_in_holiday_week(current_date):
            current_date += timedelta(days=1)
            continue

        if partner_allows_calendar_date(partner, current_date):
            candidate_dates.append(current_date)

        current_date += timedelta(days=1)

    return candidate_dates


def score_candidate(partner, event_date):
    moon_data = calculate_moon_info(
        event_date=event_date,
        timezone_name=partner.timezone,
    )

    illumination = moon_data["moon_illumination"]

    scheduling_type_score = SCHEDULING_TYPE_WEIGHT.get(
        partner.scheduling_type,
        0,
    )

    priority_score = 1000 - partner.priority

    moon_score = 0

    if partner.scheduling_type == "DARKEST":
        moon_score = 100 - illumination

    elif partner.scheduling_type == "REQUESTS_MOON":
        if 25 <= illumination <= 85:
            moon_score = 100
        else:
            moon_score = max(0, 100 - abs(55 - illumination))

    elif partner.scheduling_type == "NO_PREFERENCE":
        moon_score = 0

    return scheduling_type_score + priority_score + moon_score


def build_candidate_pool(start_date, end_date):
    candidates = []

    partners = Partner.objects.filter(
        active=True,
        partner_type="YEARLY",
    )

    for partner in partners:
        needed_count = partner.events_per_year - partner_already_has_active_suggestion(partner)

        if needed_count <= 0:
            continue

        dates = generate_partner_candidate_dates(
            partner=partner,
            start_date=start_date,
            end_date=end_date,
        )

        for event_date in dates:
            candidates.append({
                "partner": partner,
                "event_date": event_date,
                "score": score_candidate(partner, event_date),
            })

    return candidates

def get_allowed_month_numbers(partner, start_date, end_date):
    if partner.allowed_months:
        allowed_months = sorted(int(m) for m in partner.allowed_months)
    else:
        allowed_months = list(range(1, 13))

    months_in_range = []

    current_month = start_date.replace(day=1)

    while current_month <= end_date:
        if current_month.month in allowed_months:
            months_in_range.append(current_month.month)

        if current_month.month == 12:
            current_month = current_month.replace(
                year=current_month.year + 1,
                month=1,
            )
        else:
            current_month = current_month.replace(
                month=current_month.month + 1,
            )

    return sorted(set(months_in_range))

def get_target_months_for_partner(partner, start_date, end_date):
    allowed_months = get_allowed_month_numbers(partner, start_date, end_date)

    if not allowed_months:
        return []

    event_count = min(partner.events_per_year, len(allowed_months))

    if event_count <= 1:
        return [allowed_months[len(allowed_months) // 2]]

    target_months = []

    for i in range(event_count):
        index = round(i * (len(allowed_months) - 1) / (event_count - 1))
        target_months.append(allowed_months[index])

    return sorted(set(target_months))

def get_month_spacing_score(partner, event_date, target_months, selected_months):
    if partner.events_per_year > 12:
        return 0

    if event_date.month in selected_months:
        return -10000

    if not target_months:
        return 0

    closest_target_distance = min(
        abs(event_date.month - target_month)
        for target_month in target_months
    )

    return 500 - (closest_target_distance * 100)

def choose_best_candidate_for_partner_slot(
    partner,
    partner_candidates,
    target_month,
    used_dates,
    existing_suggested_dates,
    used_months,
):
    valid_candidates = []

    for candidate in partner_candidates:
        event_date = candidate["event_date"]

        if event_date in used_dates:
            continue

        if event_date in existing_suggested_dates:
            continue

        if partner.events_per_year <= 12 and event_date.month in used_months:
            continue

        month_distance = abs(event_date.month - target_month)

        valid_candidates.append({
            "candidate": candidate,
            "month_distance": month_distance,
        })

    if not valid_candidates:
        return None

    valid_candidates.sort(
        key=lambda x: (
            x["month_distance"],
            x["candidate"]["event_date"],
        )
    )

    return valid_candidates[0]["candidate"]


def calculate_suggested_event_times(partner, event_date):
    twilight_data = calculate_twilight_times(
        event_date=event_date,
        latitude=partner.latitude,
        longitude=partner.longitude,
        timezone_name=partner.timezone,
    )

    sunset_time = twilight_data["sunset_time"]

    sunset_datetime = datetime.combine(event_date, sunset_time)

    start_datetime = round_to_nearest_half_hour(sunset_datetime)

    duration_minutes = partner.minimum_event_duration_minutes or 90

    end_datetime = start_datetime + timedelta(minutes=duration_minutes)

    if partner.maximum_event_duration_minutes:
        max_end_datetime = start_datetime + timedelta(
            minutes=partner.maximum_event_duration_minutes
        )

        if end_datetime > max_end_datetime:
            end_datetime = max_end_datetime

    if partner.must_leave_by and end_datetime.time() > partner.must_leave_by:
        end_datetime = datetime.combine(event_date, partner.must_leave_by)

    return {
        "sunset_time": sunset_time,
        "start_time": start_datetime.time(),
        "end_time": end_datetime.time(),
    }


def optimize_suggested_events(start_date, end_date, dry_run=True, scheduler_run=None):
    candidates = build_candidate_pool(start_date, end_date)

    selected = []
    used_dates = set()

    existing_suggested_dates = set(
        SuggestedEvent.objects.filter(
            status__in=["SUGGESTED", "APPROVED"],
            suggested_date__gte=start_date,
            suggested_date__lte=end_date,
        ).values_list("suggested_date", flat=True)
    )

    partners = Partner.objects.filter(
        active=True,
        partner_type="YEARLY",
    ).order_by(
        "scheduling_type",
        "priority",
        "partner_name",
    )

    for partner in partners:
        already_active_count = SuggestedEvent.objects.filter(
            partner=partner,
            status__in=["SUGGESTED", "APPROVED"],
            suggested_date__gte=start_date,
            suggested_date__lte=end_date,
        ).count()

        needed_count = partner.events_per_year - already_active_count

        if needed_count <= 0:
            continue

        partner_candidates = [
            c for c in candidates
            if c["partner"].id == partner.id
        ]

        target_months = get_target_months_for_partner(
            partner,
            start_date,
            end_date,
        )

        target_months = target_months[:needed_count]

        used_months = set(
            SuggestedEvent.objects.filter(
                partner=partner,
                status__in=["SUGGESTED", "APPROVED"],
                suggested_date__gte=start_date,
                suggested_date__lte=end_date,
            ).values_list("suggested_date__month", flat=True)
        )

        for target_month in target_months:
            chosen = choose_best_candidate_for_partner_slot(
                partner=partner,
                partner_candidates=partner_candidates,
                target_month=target_month,
                used_dates=used_dates,
                existing_suggested_dates=existing_suggested_dates,
                used_months=used_months,
            )

            if not chosen:
                continue

            selected.append(chosen)
            used_dates.add(chosen["event_date"])
            used_months.add(chosen["event_date"].month)

    if not dry_run:
        for item in selected:
            time_data = calculate_suggested_event_times(
                partner=item["partner"],
                event_date=item["event_date"],
            )

            SuggestedEvent.objects.get_or_create(
                partner=item["partner"],
                suggested_date=item["event_date"],
                defaults={
                    "status": "SUGGESTED",
                    "scheduler_run": scheduler_run,
                    "sunset_time": time_data["sunset_time"],
                    "start_time": time_data["start_time"],
                    "end_time": time_data["end_time"],
                },
            )

    return selected
