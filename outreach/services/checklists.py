from datetime import timedelta

from outreach.models import EventChecklistItem


GENERAL_CHECKLIST_ITEMS = [
    {
        "title": "Send email volunteer request",
        "description": "Send initial volunteer request.",
        "days_before_event": 10,
    },
    {
        "title": "Check for volunteer request failures and resend",
        "description": "Confirm volunteer request went out successfully and resend if needed.",
        "days_before_event": 9,
    },
    {
        "title": "Confirm venue info links on AAS website calendar",
        "description": "Check that venue and event links on the AAS website calendar work properly.",
        "days_before_event": 10,
    },
    {
        "title": "Create and post event on AAS Facebook page",
        "description": "Create or confirm Facebook event/post.",
        "days_before_event": 10,
    },
    {
        "title": "Create/post/check event on Night Sky Network calendar",
        "description": "If public event, create or verify the Night Sky Network calendar entry.",
        "days_before_event": 10,
    },
    {
        "title": "Make modified star chart for laser tour",
        "description": "Generate or prepare the modified star chart. Eventually automated in app.",
        "days_before_event": 7,
    },
    {
        "title": "Send additional volunteer request if needed",
        "description": "Send another volunteer request if coverage is still short.",
        "days_before_event": 4,
    },
    {
        "title": "Weather check-in with organizer",
        "description": "By 1 PM the day before, check weather with organizer for CONFIRM or CANCEL decision.",
        "days_before_event": 1,
    },
    {
        "title": "Second Facebook post confirming event is go",
        "description": "Post day-before confirmation that the event is still happening.",
        "days_before_event": 1,
    },
    {
        "title": "Day-of GO / NO-GO email to AAS members",
        "description": "By 1 PM day of event, email members with last-minute GO / NO-GO status.",
        "days_before_event": 0,
    },
]


CANCELLATION_CHECKLIST_ITEMS = [
    {
        "title": "Edit AAS website calendar and event page to show CANCELLED",
        "description": "Update the AAS website event listing.",
        "days_before_event": 1,
    },
    {
        "title": "Edit Night Sky Network event to show cancelled",
        "description": "Update the Night Sky Network calendar entry.",
        "days_before_event": 1,
    },
    {
        "title": "Edit Facebook event to show cancelled",
        "description": "Mark Facebook event cancelled and post cancellation notification.",
        "days_before_event": 1,
    },
    {
        "title": "Send cancellation email to all members",
        "description": "Day before event, send mass email notifying members of cancellation.",
        "days_before_event": 1,
    },
]


PFSP_CHECKLIST_ITEMS = [
    {
        "title": "PFSP: Check registration page link",
        "description": "Two weeks before, check AAS calendar link to PFSP registration page.",
        "days_before_event": 14,
    },
    {
        "title": "PFSP: Send volunteer list",
        "description": "Send volunteer list by email Friday or Saturday by 2 PM.",
        "days_before_event": 1,
    },
]


CAMPING_CHECKLIST_ITEMS = {
    "PFSP": [
        {
            "title": "PFSP camping: Send camper list",
            "description": "Send list of campers to park interpreter up to day of event.",
            "days_before_event": 0,
        },
    ],
    "ILSP": [
        {
            "title": "ILSP camping: Send camper list",
            "description": "Send list of campers to park interpreter by Wednesday noon.",
            "days_before_event": 3,
        },
    ],
    "EROCK": [
        {
            "title": "ERock camping: Send camper list",
            "description": "Send list of campers to park interpreter by Saturday before event.",
            "days_before_event": 7,
        },
    ],
    "BLANCO": [
        {
            "title": "Blanco SP camping: Send camper list",
            "description": "Send list of campers to park interpreter by Wednesday noon.",
            "days_before_event": 3,
        },
    ],
}


def create_items(event, items, cancellation_item=False):
    created_items = []

    for item in items:
        due_date = event.event_date - timedelta(days=item["days_before_event"])

        checklist_item, created = EventChecklistItem.objects.get_or_create(
            event=event,
            title=item["title"],
            defaults={
                "description": item["description"],
                "days_before_event": item["days_before_event"],
                "due_date": due_date,
                "cancellation_item": cancellation_item,
            },
        )

        if created:
            created_items.append(checklist_item)

    return created_items


def partner_matches(event, text):
    partner_text = (
        f"{event.partner.partner_name} "
        f"{event.partner.location_name} "
        f"{event.partner.notes}"
    ).upper()

    return text.upper() in partner_text


def create_checklist_items_for_event(event):
    created_items = []

    created_items.extend(
        create_items(event, GENERAL_CHECKLIST_ITEMS)
    )

    if partner_matches(event, "Pedernales") or partner_matches(event, "PFSP"):
        created_items.extend(
            create_items(event, PFSP_CHECKLIST_ITEMS)
        )

    if partner_matches(event, "PFSP"):
        created_items.extend(
            create_items(event, CAMPING_CHECKLIST_ITEMS["PFSP"])
        )

    if partner_matches(event, "ILSP"):
        created_items.extend(
            create_items(event, CAMPING_CHECKLIST_ITEMS["ILSP"])
        )

    if partner_matches(event, "EROCK") or partner_matches(event, "Enchanted Rock"):
        created_items.extend(
            create_items(event, CAMPING_CHECKLIST_ITEMS["EROCK"])
        )

    if partner_matches(event, "Blanco"):
        created_items.extend(
            create_items(event, CAMPING_CHECKLIST_ITEMS["BLANCO"])
        )

    return created_items


def create_cancellation_checklist_items_for_event(event):
    return create_items(
        event,
        CANCELLATION_CHECKLIST_ITEMS,
        cancellation_item=True,
    )