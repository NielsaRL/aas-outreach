## code for determining what objects to target during the start party based on location, and date/time

from outreach.models import AstronomicalTarget, EventTarget
from outreach.services.dynamic_targets import get_visible_solar_system_targets
from outreach.services.visibility import get_target_visibility_window_for_event


def target_matches_event(target, event):
    event_month = str(event.event_date.month)

    if target.best_months and event_month not in target.best_months:
        return False

    if target.discussion_only:
        return True

    if event.moon_illumination is not None and event.moon_illumination > 60:
        if target.target_type in ["DSO", "COMET"]:
            return False

    return True


def upsert_event_target(
    event,
    target,
    can_observe,
    good_talking_point,
    notes,
    altitude=None,
    azimuth=None,
    visible_start_time=None,
    visible_end_time=None,
):
    event_target, created = EventTarget.objects.get_or_create(
        event=event,
        target=target,
    )

    event_target.can_observe_during_event = can_observe
    event_target.good_talking_point = good_talking_point
    event_target.notes = notes
    event_target.altitude_degrees = altitude
    event_target.azimuth_degrees = azimuth
    event_target.visible_start_time = visible_start_time
    event_target.visible_end_time = visible_end_time
    event_target.save()

    return event_target, created


def suggest_curated_targets_for_event(event, max_targets=5):
    targets = AstronomicalTarget.objects.filter(
        active=True,
    ).order_by(
        "target_type",
        "name",
    )

    added_or_updated = []

    for target in targets:
        if not target_matches_event(target, event):
            continue

        visibility_window = get_target_visibility_window_for_event(
            event=event,
            target=target,
            minimum_altitude=20,
        )

        if not target.discussion_only and visibility_window is None:
            continue

        event_target, created = upsert_event_target(
            event=event,
            target=target,
            can_observe=target.visible_during_event,
            good_talking_point=True,
            notes=target.outreach_notes,
            altitude=visibility_window["altitude"] if visibility_window else None,
            azimuth=visibility_window["azimuth"] if visibility_window else None,
            visible_start_time=visibility_window["visible_start_time"] if visibility_window else None,
            visible_end_time=visibility_window["visible_end_time"] if visibility_window else None,
        )

        added_or_updated.append(target)

        if len(added_or_updated) >= max_targets:
            break

    return added_or_updated


def suggest_dynamic_targets_for_event(event):
    added_or_updated = []

    dynamic_targets = get_visible_solar_system_targets(event)

    for dynamic_target in dynamic_targets:
        target, _ = AstronomicalTarget.objects.get_or_create(
            name=dynamic_target["name"],
            defaults={
                "target_type": dynamic_target["target_type"],
                "constellation": "",
                "best_months": [],
                "visible_during_event": True,
                "discussion_only": False,
                "outreach_notes": dynamic_target["notes"],
                "active": True,
            },
        )

        event_target, created = upsert_event_target(
            event=event,
            target=target,
            can_observe=True,
            good_talking_point=True,
            notes=dynamic_target["notes"],
            altitude=dynamic_target.get("altitude"),
            azimuth=dynamic_target.get("azimuth"),
            visible_start_time=event.start_time,
            visible_end_time=event.end_time,
        )

        added_or_updated.append(target)

    return added_or_updated


def suggest_targets_for_event(event, max_targets=5):
    added_or_updated = []

    added_or_updated.extend(
        suggest_curated_targets_for_event(
            event=event,
            max_targets=max_targets,
        )
    )

    added_or_updated.extend(
        suggest_dynamic_targets_for_event(event)
    )

    return added_or_updated