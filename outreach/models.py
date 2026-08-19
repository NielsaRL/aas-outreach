from django.db import models
from datetime import datetime
from .services.astronomy import calculate_twilight_times, calculate_moon_info
from django.core.exceptions import ValidationError
from multiselectfield import MultiSelectField
from django.contrib.auth.models import User
from django.db.models import Sum


# Create your models here.
class Partner(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["partner_type", "scheduling_type", "priority"],
                name="unique_partner_type_scheduling_type_priority",
            )
        ]

    PARTNER_TYPE_CHOICES = [
        ("YEARLY", "Yearly Partner"),
        ("AD_HOC", "Ad Hoc Event Requestor"),
    ]

    SCHEDULING_TYPE_CHOICES = [
        ("DARKEST", "Darkest Moon"),
        ("REQUESTS_MOON", "Requests some Moon"),
        ("NO_PREFERENCE", "No Preference"),
        ("CUSTOM", "Custom Rule"),
    ]

    partner_name = models.CharField(max_length=200)

    partner_type = models.CharField(
        max_length=20,
        choices=PARTNER_TYPE_CHOICES,
        default="YEARLY"
    )

    scheduling_type = models.CharField(
        max_length=30,
        choices=SCHEDULING_TYPE_CHOICES,
        default="DARKEST"
    )

    priority = models.IntegerField(default=3)
    events_per_year = models.IntegerField(default=1)

    WEEKDAY_CHOICES = [
        ("0", "Monday"),
        ("1", "Tuesday"),
        ("2", "Wednesday"),
        ("3", "Thursday"),
        ("4", "Friday"),
        ("5", "Saturday"),
        ("6", "Sunday"),
    ]

    allowed_weekdays = MultiSelectField(
        choices=WEEKDAY_CHOICES,
        blank=True,
    )

    OCCURRENCE_CHOICES = [
        ("1", "First"),
        ("2", "Second"),
        ("3", "Third"),
        ("4", "Fourth"),
        ("5", "Fifth"),
        ("LAST", "Last"),
    ]

    allowed_weekday_occurrences = MultiSelectField(
        choices=OCCURRENCE_CHOICES,
        blank=True,
    )

    MONTH_CHOICES = [
        ("1", "January"),
        ("2", "February"),
        ("3", "March"),
        ("4", "April"),
        ("5", "May"),
        ("6", "June"),
        ("7", "July"),
        ("8", "August"),
        ("9", "September"),
        ("10", "October"),
        ("11", "November"),
        ("12", "December"),
    ]

    allowed_months = MultiSelectField(
        choices=MONTH_CHOICES,
        blank=True,
    )
    minimum_event_duration_minutes = models.IntegerField(
        null=True,
        blank=True,
        help_text="Minimum event duration in minutes. Example: 90"
    )

    maximum_event_duration_minutes = models.IntegerField(
        null=True,
        blank=True,
        help_text="Maximum event duration in minutes. Example: 180"
    )

    must_leave_by = models.TimeField(
        null=True,
        blank=True,
        help_text="Latest time the club must be off-site."
    )

    # Location info
    location_name = models.CharField(max_length=200, blank=True)
    address = models.CharField(max_length=500, blank=True)

    sky_brightness_sqm = models.FloatField(
        null=True,
        blank=True,
        help_text="Estimated sky brightness in mag/arcsec²."
    )

    auto_bortle_class = models.FloatField(
        null=True,
        blank=True,
        editable=False,
        help_text="Estimated Bortle class based on sky brightness."
    )

    latitude = models.FloatField(
        null=True,
        blank=True
    )

    longitude = models.FloatField(
        null=True,
        blank=True,
        help_text="Use negative longitude for North America, example: -97.7431"
    )

    timezone = models.CharField(
        max_length=100,
        default="America/Chicago"
    )

    # Contact info
    contact_name = models.CharField(max_length=200, blank=True)
    contact_role_title = models.CharField(max_length=200, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)

    active = models.BooleanField(default=True)
    volunteer_arrival_instructions = models.TextField(
        blank=True,
        help_text="Recurring arrival instructions for volunteers at this partner/location."
    )

    meeting_location = models.CharField(
        max_length=200,
        blank=True,
        help_text="Where volunteers should meet upon arrival."
    )

    parking_instructions = models.TextField(
        blank=True,
        help_text="Recurring parking instructions for this partner/location."
    )

    setup_location_notes = models.TextField(
        blank=True,
        help_text="Recurring setup notes, such as where telescopes, tables, or check-in should go."
    )

    notes = models.TextField(blank=True)

    def clean(self):
        if self.latitude is not None:
            if not (-90 <= self.latitude <= 90):
                raise ValidationError(
                    "Latitude must be between -90 and 90 degrees."
                )

            if not (15 <= self.latitude <= 75):
                raise ValidationError(
                    "Latitude appears outside the expected US range."
                )

        if self.longitude is not None:
            if not (-180 <= self.longitude <= 180):
                raise ValidationError(
                    "Longitude must be between -180 and 180 degrees."
                )

            if self.longitude > 0:
                raise ValidationError(
                    "Longitude should be negative for North American locations."
                )

    def __str__(self):
        return self.partner_name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

class Volunteer(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="volunteer_profile",
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)

    equipment_owned = models.TextField(
        blank=True,
        help_text="List equipment this volunteer owns, one item per line."
    )

    active = models.BooleanField(default=True)

    host_trained = models.BooleanField(
        default=False,
        help_text="Check if this volunteer is trained to host events."
    )

    outreach_committee = models.BooleanField(
        default=False,
        help_text="Member of the AAS Outreach Committee"
    )

    cleared_by_pfsp = models.BooleanField(
        default=False,
        help_text="Check if this volunteer is cleared by PFSP."
    )

    notes = models.TextField(blank=True)

    @property
    def volunteer_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def save(self, *args, **kwargs):
        if self.phone:
            digits = "".join(
                character
                for character in self.phone
                if character.isdigit()
            )

            if len(digits) == 10:
                self.phone = (
                    f"{digits[:3]}-"
                    f"{digits[3:6]}-"
                    f"{digits[6:]}"
                )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.volunteer_name

class ScheduledEvent(models.Model):

    STATUS_CHOICES = [
        ("PLANNED", "Planned"),
        ("CONFIRMED", "Confirmed"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    EVENT_TITLE_CHOICES = [
        ("STAR_PARTY", "Star Party"),
        ("SOLAR_OUTREACH", "Solar Outreach"),
        ("LIBRARY_PROGRAM", "Library Program"),
        ("SIDEWALK_ASTRONOMY", "Sidewalk Astronomy"),
        ("CUSTOM", "Custom"),
    ]

    partner = models.ForeignKey(
        Partner,
        on_delete=models.CASCADE
    )

    event_title_type = models.CharField(
        max_length=30,
        choices=EVENT_TITLE_CHOICES,
        default="STAR_PARTY"
    )

    custom_event_title = models.CharField(
        max_length=100,
        blank=True,
        help_text="Only use this if Event title type is Custom."
    )

    event_name = models.CharField(
        max_length=200,
        editable=False
    )

    event_date = models.DateField()

    date_confirmed = models.BooleanField(
        default=False,
        help_text="Check this once the event date has been confirmed."
    )

    host = models.ForeignKey(
        Volunteer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hosted_events",
        limit_choices_to={
            "active": True,
            "host_trained": True,
        },
        help_text="Select the trained AAS host, if applicable."
    )

    manual_host_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Use this for private parties or events hosted by someone not in the volunteer list."
    )

    sunset_time = models.TimeField(null=True, blank=True)
    civil_dusk_time = models.TimeField(null=True, blank=True)
    nautical_dusk_time = models.TimeField(null=True, blank=True)

    moon_phase = models.CharField(
        max_length=50,
        blank=True
    )

    moon_illumination = models.FloatField(
        null=True,
        blank=True,
        help_text="Moon illumination percentage."
    )

    suggested_talk_start_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Suggested 30-minute talk start time."
    )

    suggested_laser_tour_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Suggested laser constellation tour start time."
    )
    start_time = models.TimeField(
        null=True,
        blank=True
    )

    end_time = models.TimeField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PLANNED"
    )

    advertising_radius_miles = models.PositiveIntegerField(
        default=25,
    )

    advertise_to_full_service_area = models.BooleanField(
        default=False,
    )

    expected_attendance = models.IntegerField(
        null=True,
        blank=True
    )

    weather_heat_index_f = models.FloatField(null=True, blank=True)
    weather_temperature_f = models.FloatField(null=True, blank=True)
    weather_wind_speed_mph = models.FloatField(null=True, blank=True)
    weather_precipitation_probability = models.IntegerField(null=True, blank=True)
    weather_cloud_cover_percent = models.IntegerField(null=True, blank=True)

    weather_rain_text = models.CharField(max_length=100, blank=True)
    weather_thunder_text = models.CharField(max_length=100, blank=True)

    weather_watch_text = models.CharField(max_length=255, blank=True)
    weather_warning_text = models.CharField(max_length=255, blank=True)
    weather_summary = models.CharField(max_length=255, blank=True)
    weather_last_checked = models.DateTimeField(null=True, blank=True)
    event_specific_instructions = models.TextField(
        blank=True,
        help_text="Special instructions for this event only. Use the Partner record for recurring location instructions."
    )
    notes = models.TextField(blank=True)

    def host_display(self):
        if self.host:
            return self.host.volunteer_name
        if self.manual_host_name:
            return self.manual_host_name
        return "No host assigned"

    def save(self, *args, **kwargs):
        formatted_date = self.event_date.strftime("%B %d, %Y")

        title_label = dict(self.EVENT_TITLE_CHOICES).get(
            self.event_title_type,
            "Star Party"
        )

        if self.event_title_type == "CUSTOM" and self.custom_event_title:
            title_label = self.custom_event_title

        location_label = self.partner.location_name or self.partner.partner_name

        self.event_name = (
            f"{location_label} "
            f"{title_label} - "
            f"{formatted_date}"
        )

        if self.event_date and self.partner:
            twilight_data = calculate_twilight_times(
                event_date=self.event_date,
                latitude=self.partner.latitude,
                longitude=self.partner.longitude,
                timezone_name=self.partner.timezone,
            )

            self.sunset_time = twilight_data["sunset_time"]
            self.civil_dusk_time = twilight_data["civil_dusk_time"]
            self.nautical_dusk_time = twilight_data["nautical_dusk_time"]
            self.suggested_talk_start_time = twilight_data["suggested_talk_start_time"]
            self.suggested_laser_tour_time = twilight_data["suggested_laser_tour_time"]
            moon_data = calculate_moon_info(
                event_date=self.event_date,
                timezone_name=self.partner.timezone,
            )

            self.moon_phase = moon_data["moon_phase"]
            self.moon_illumination = moon_data["moon_illumination"]

        super().save(*args, **kwargs)

        from outreach.services.checklists import (
            create_checklist_items_for_event,
            create_cancellation_checklist_items_for_event,
        )

        create_checklist_items_for_event(self)

        if self.status == "CANCELLED":
            create_cancellation_checklist_items_for_event(self)

        if self.status == "CONFIRMED":
            EventLog.objects.get_or_create(event=self)

    volunteer_capacity = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum number of volunteers allowed to sign up. Leave blank for unlimited.",
    )

    @property
    def volunteer_count(self):
        return self.event_volunteers.count()

    @property
    def volunteer_spots_remaining(self):
        if self.volunteer_capacity is None:
            return None

        return max(
            self.volunteer_capacity - self.volunteer_count,
            0,
        )

    @property
    def volunteer_signup_full(self):
        if self.volunteer_capacity is None:
            return False

        return self.volunteer_count >= self.volunteer_capacity

    @property
    def telescope_count(self):
        total = self.event_volunteers.aggregate(
            total=Sum("telescope_count")
        )["total"]

        return total or 0

    def __str__(self):
        return self.event_name

class EventChecklist(ScheduledEvent):
    class Meta:
        proxy = True
        verbose_name = "Event Checklist"
        verbose_name_plural = "Event Checklists"

class BlackoutDate(models.Model):
    blackout_date = models.DateField(
        unique=True,
        help_text="Date that should not be used by the yearly scheduler.",
    )

    reason = models.CharField(
        max_length=255,
        help_text="Reason this date is unavailable.",
    )

    active = models.BooleanField(
        default=True,
        help_text="Uncheck to allow this date to be scheduled without deleting the blackout record.",
    )

    class Meta:
        ordering = ("blackout_date",)
        verbose_name = "Blackout Date"
        verbose_name_plural = "Blackout Dates"

    def __str__(self):
        return f"{self.blackout_date} — {self.reason}"


class EventVolunteer(models.Model):

    ROLE_CHOICES = [
        ("TELESCOPE", "Telescope"),
        ("SUPPORT", "Welcome / Junior Astronomy Display/ Telescope Petting Zoo"),
        ("OTHER", "Other"),
    ]

    event = models.ForeignKey(
        ScheduledEvent,
        on_delete=models.CASCADE,
        related_name="event_volunteers",
    )

    volunteer = models.ForeignKey(
        Volunteer,
        on_delete=models.CASCADE,
        related_name="event_assignments",
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="TELESCOPE",
    )

    telescope_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of telescopes this volunteer plans to bring.",
    )

    notes = models.TextField(blank=True)

    def clean(self):
        super().clean()

        if self.role == "TELESCOPE":
            if self.telescope_count is None or self.telescope_count < 1:
                raise ValidationError(
                    {
                        "telescope_count": (
                            "Telescope volunteers must bring at least one telescope."
                        )
                    }
                )
        else:
            self.telescope_count = None

    def __str__(self):
        return f"{self.volunteer.volunteer_name} - {self.event.event_name}"

class EventLog(models.Model):

    event = models.OneToOneField(
        ScheduledEvent,
        on_delete=models.CASCADE,
        related_name="event_log"
    )

    actual_start_time = models.TimeField(
        null=True,
        blank=True
    )

    actual_end_time = models.TimeField(
        null=True,
        blank=True
    )

    attendance = models.IntegerField(
        null=True,
        blank=True
    )

    weather_conditions = models.CharField(
        max_length=200,
        blank=True
    )

    sky_conditions = models.CharField(
        max_length=200,
        blank=True
    )

    notes = models.TextField(blank=True)

    follow_up_needed = models.TextField(blank=True)

    def __str__(self):
        return (
            f"{self.event.partner.partner_name} - "
            f"{self.event.event_name} "
            f"({self.event.event_date})"
        )

class AstronomicalTarget(models.Model):

    TARGET_TYPE_CHOICES = [
        ("PLANET", "Planet"),
        ("METEOR_SHOWER", "Meteor Shower"),
        ("DSO", "Deep Sky Object"),
        ("COMET", "Comet"),
        ("ECLIPSE", "Eclipse"),
        ("CONSTELLATION", "Constellation"),
        ("MOON", "Moon"),
        ("OTHER", "Other"),
    ]

    name = models.CharField(max_length=200)

    target_type = models.CharField(
        max_length=30,
        choices=TARGET_TYPE_CHOICES
    )

    constellation = models.CharField(
        max_length=100,
        blank=True
    )

    MONTH_CHOICES = [
        ("1", "January"),
        ("2", "February"),
        ("3", "March"),
        ("4", "April"),
        ("5", "May"),
        ("6", "June"),
        ("7", "July"),
        ("8", "August"),
        ("9", "September"),
        ("10", "October"),
        ("11", "November"),
        ("12", "December"),
    ]

    best_months = MultiSelectField(
        choices=MONTH_CHOICES,
        blank=True,
        help_text="Leave blank if this target is useful year-round."
    )

    visible_during_event = models.BooleanField(
        default=True,
        help_text="Check if this is usually something to observe, not just discuss."
    )

    discussion_only = models.BooleanField(
        default=False,
        help_text="Check if this is mainly an interesting talking point."
    )

    outreach_notes = models.TextField(
        blank=True,
        help_text="Public-friendly notes or talking points."
    )

    active = models.BooleanField(default=True)

    ra_hours = models.FloatField(null=True, blank=True)
    dec_degrees = models.FloatField(null=True, blank=True)

    representative_point = models.CharField(
        max_length=100,
        blank=True,
        help_text="What these coordinates represent."
    )

    def __str__(self):
        return f"{self.name} ({self.get_target_type_display()})"

class EventTarget(models.Model):
    event = models.ForeignKey(
        ScheduledEvent,
        on_delete=models.CASCADE,
        related_name="event_targets"
    )

    target = models.ForeignKey(
        AstronomicalTarget,
        on_delete=models.CASCADE,
        related_name="event_appearances"
    )

    can_observe_during_event = models.BooleanField(default=True)

    good_talking_point = models.BooleanField(default=True)

    altitude_degrees = models.FloatField(null=True, blank=True)

    azimuth_degrees = models.FloatField(null=True, blank=True)

    visible_start_time = models.TimeField(null=True, blank=True)
    visible_end_time = models.TimeField(null=True, blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "target"],
                name="unique_event_target",
            )
        ]

    def __str__(self):
        return f"{self.event.event_name} - {self.target.name}"

class SuggestedEvent(models.Model):

    STATUS_CHOICES = [
        ("SUGGESTED", "Suggested"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    partner = models.ForeignKey(
        Partner,
        on_delete=models.CASCADE,
        related_name="suggested_events",
    )
    scheduler_run = models.ForeignKey(
        "SchedulerRun",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="suggested_events",
    )

    suggested_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    sunset_time = models.TimeField(null=True, blank=True)

    manual_entry = models.BooleanField(
        default=False,
        help_text="Check if this suggestion was manually entered and should be preserved."
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="SUGGESTED",
    )

    rejection_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["partner", "suggested_date"],
                name="unique_partner_suggested_date",
            )
        ]

    def __str__(self):
        return f"{self.partner.partner_name} - {self.suggested_date} ({self.status})"

class SchedulerRun(models.Model):

    start_date = models.DateField()
    end_date = models.DateField()

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    run_scheduler = models.BooleanField(
        default=False,
        help_text="Check this and save to generate suggested events for this date range."
    )

    def save(self, *args, **kwargs):
        should_run = self.run_scheduler

        self.run_scheduler = False

        super().save(*args, **kwargs)

        if should_run:
            from .services.scheduler import optimize_suggested_events

            optimize_suggested_events(
                start_date=self.start_date,
                end_date=self.end_date,
                dry_run=False,
                scheduler_run=self,
            )

    def __str__(self):
        return f"Scheduler Run: {self.start_date} to {self.end_date}"

class EventChecklistItem(models.Model):
    STATUS_CHOICES = [
        ("TODO", "To Do"),
        ("DONE", "Completed"),
        ("NA", "Not Applicable"),
    ]

    event = models.ForeignKey(
        ScheduledEvent,
        on_delete=models.CASCADE,
        related_name="checklist_items",
    )

    title = models.CharField(max_length=200)

    description = models.TextField(blank=True)

    due_date = models.DateField(
        null=True,
        blank=True,
    )

    days_before_event = models.IntegerField(
        null=True,
        blank=True,
        help_text="Example: 10 means due 10 days before the event.",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="TODO",
    )

    cancellation_item = models.BooleanField(
        default=False,
        help_text="Checked if this item was added because the event was cancelled.",
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["due_date", "days_before_event", "title"]

    def __str__(self):
        return f"{self.event.event_name} - {self.title}"

class AdvertisingOutlet(models.Model):
    class SubmissionMethod(models.TextChoices):
        API = "API", "Fully Automated / API"
        BROWSER = "BROWSER", "Browser Assisted"
        EMAIL = "EMAIL", "Email"
        MANUAL_FORM = "MANUAL_FORM", "Manual Web Form"
        SOCIAL = "SOCIAL", "Manual Social Media Post"
        PHONE = "PHONE", "Phone"
        OTHER = "OTHER", "Other"

    class Category(models.TextChoices):
        COMMUNITY_CALENDAR = "COMMUNITY_CALENDAR", "Community Calendar"
        NEWS_MEDIA = "NEWS_MEDIA", "News or Media"
        SOCIAL_MEDIA = "SOCIAL_MEDIA", "Social Media"
        LIBRARY = "LIBRARY", "Library"
        SCHOOL = "SCHOOL", "School or Education"
        PARKS_OUTDOORS = "PARKS_OUTDOORS", "Parks or Outdoors"
        SCIENCE = "SCIENCE", "Science Organization"
        FAMILY = "FAMILY", "Family Activities"
        TOURISM = "TOURISM", "Tourism"
        PARTNER = "PARTNER", "Partner Organization"
        OTHER = "OTHER", "Other"

    class Priority(models.IntegerChoices):
        CRITICAL = 1, "Critical"
        HIGH = 2, "High"
        NORMAL = 3, "Normal"
        LOW = 4, "Low"

    name = models.CharField(
        max_length=200,
        unique=True,
    )

    category = models.CharField(
        max_length=30,
        choices=Category.choices,
        default=Category.COMMUNITY_CALENDAR,
    )

    submission_method = models.CharField(
        max_length=30,
        choices=SubmissionMethod.choices,
        default=SubmissionMethod.MANUAL_FORM,
    )

    priority = models.PositiveSmallIntegerField(
        choices=Priority.choices,
        default=Priority.NORMAL,
    )

    website_url = models.URLField(
        blank=True,
    )

    submission_url = models.URLField(
        blank=True,
        help_text="Direct link to the event submission page, when available.",
    )

    contact_name = models.CharField(
        max_length=200,
        blank=True,
    )

    contact_email = models.EmailField(
        blank=True,
    )

    contact_phone = models.CharField(
        max_length=50,
        blank=True,
    )

    city = models.CharField(
        max_length=100,
        blank=True,
    )

    county = models.CharField(
        max_length=100,
        blank=True,
    )

    state = models.CharField(
        max_length=50,
        default="Texas",
        blank=True,
    )

    service_radius_miles = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=(
            "Approximate distance from the outlet's city that it covers. "
            "Leave blank for outlets that are not geographically limited."
        ),
    )

    minimum_lead_days = models.PositiveIntegerField(
        default=0,
        help_text=(
            "Minimum number of days before an event that it should be submitted."
        ),
    )

    preferred_lead_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Preferred number of days before an event for submission.",
    )

    accepts_star_parties = models.BooleanField(default=True)
    accepts_solar_outreach = models.BooleanField(default=True)
    accepts_library_programs = models.BooleanField(default=True)
    accepts_sidewalk_astronomy = models.BooleanField(default=True)
    accepts_custom_events = models.BooleanField(default=True)

    requires_account = models.BooleanField(default=False)
    requires_image = models.BooleanField(default=False)
    requires_approval = models.BooleanField(default=False)

    covers_full_service_area = models.BooleanField(
        default=False,
    )

    estimated_submission_minutes = models.PositiveIntegerField(
        default=5,
    )

    # ---------------------------------------------------------
    # Content and formatting requirements
    # ---------------------------------------------------------

    maximum_title_characters = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=(
            "Maximum number of characters allowed in the event title. "
            "Leave blank when there is no known limit."
        ),
    )

    maximum_description_characters = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=(
            "Maximum number of characters allowed in the event description. "
            "Leave blank when there is no known limit."
        ),
    )

    allows_images = models.BooleanField(
        default=True,
        help_text="Whether the outlet allows an image to be submitted.",
    )

    allows_links = models.BooleanField(
        default=True,
        help_text="Whether links may be included in the submitted copy.",
    )

    allows_html = models.BooleanField(
        default=False,
        help_text="Whether the description field accepts HTML formatting.",
    )

    allows_emojis = models.BooleanField(
        default=False,
        help_text="Whether emojis are appropriate for this outlet.",
    )

    allows_hashtags = models.BooleanField(
        default=False,
        help_text="Whether hashtags are appropriate for this outlet.",
    )

    requires_plain_text = models.BooleanField(
        default=True,
        help_text="Whether submitted copy should be plain text only.",
    )

    content_guidance = models.TextField(
        blank=True,
        help_text=(
            "Outlet-specific writing rules, required details, tone, "
            "formatting guidance, or prohibited content."
        ),
    )

    # ---------------------------------------------------------
    # Submission requirements
    # ---------------------------------------------------------

    requires_event_title = models.BooleanField(default=True)
    requires_description = models.BooleanField(default=True)
    requires_start_time = models.BooleanField(default=True)
    requires_end_time = models.BooleanField(default=False)
    requires_address = models.BooleanField(default=True)
    requires_cost = models.BooleanField(default=False)
    requires_contact_email = models.BooleanField(default=False)
    requires_contact_phone = models.BooleanField(default=False)
    requires_registration_url = models.BooleanField(default=False)

    requires_captcha = models.BooleanField(
        default=False,
        help_text=(
            "Whether the submission form normally requires manual CAPTCHA "
            "completion."
        ),
    )

    # ---------------------------------------------------------
    # Verification and maintenance
    # ---------------------------------------------------------

    last_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=(
            "The last date and time the submission instructions were verified."
        ),
    )

    verification_notes = models.TextField(
        blank=True,
        help_text=(
            "Notes about the latest review of this outlet's submission process."
        ),
    )

    active = models.BooleanField(default=True)

    submission_instructions = models.TextField(
        blank=True,
        help_text="Instructions for submitting an event to this outlet.",
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["priority", "name"]
        verbose_name = "Advertising Outlet"
        verbose_name_plural = "Advertising Outlets"

    def accepts_event_type(self, event_title_type):
        event_type_fields = {
            "STAR_PARTY": self.accepts_star_parties,
            "SOLAR_OUTREACH": self.accepts_solar_outreach,
            "LIBRARY_PROGRAM": self.accepts_library_programs,
            "SIDEWALK_ASTRONOMY": self.accepts_sidewalk_astronomy,
            "CUSTOM": self.accepts_custom_events,
        }

        return event_type_fields.get(event_title_type, False)

    def __str__(self):
        return self.name

class AdvertisingCampaign(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        COMPLETE = "COMPLETE", "Complete"
        CANCELLED = "CANCELLED", "Cancelled"

    event = models.OneToOneField(
        ScheduledEvent,
        on_delete=models.CASCADE,
        related_name="advertising_campaign",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    generated_at = models.DateTimeField(auto_now_add=True)

    generated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="generated_advertising_campaigns",
    )

    last_regenerated_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["event__event_date", "event__event_name"]
        verbose_name = "Advertising Campaign"
        verbose_name_plural = "Advertising Campaigns"

    @property
    def total_outlets(self):
        return self.advertisements.count()

    @property
    def completed_outlets(self):
        return self.advertisements.filter(
            status__in=[
                EventAdvertisement.Status.PUBLISHED,
                EventAdvertisement.Status.SKIPPED,
                EventAdvertisement.Status.NOT_APPLICABLE,
            ]
        ).count()

    @property
    def progress_percent(self):
        total = self.total_outlets

        if total == 0:
            return 0

        return round((self.completed_outlets / total) * 100)

    @property
    def not_started_count(self):
        return self.advertisements.filter(
            status=EventAdvertisement.Status.NOT_STARTED
        ).count()

    @property
    def ready_count(self):
        return self.advertisements.filter(
            status=EventAdvertisement.Status.READY
        ).count()

    @property
    def submitted_count(self):
        return self.advertisements.filter(
            status=EventAdvertisement.Status.SUBMITTED
        ).count()

    @property
    def published_count(self):
        return self.advertisements.filter(
            status=EventAdvertisement.Status.PUBLISHED
        ).count()

    @property
    def skipped_count(self):
        return self.advertisements.filter(
            status=EventAdvertisement.Status.SKIPPED
        ).count()

    @property
    def remaining_count(self):
        completed_statuses = [
            EventAdvertisement.Status.PUBLISHED,
            EventAdvertisement.Status.SKIPPED,
            EventAdvertisement.Status.NOT_APPLICABLE,
        ]

        return self.advertisements.exclude(
            status__in=completed_statuses
        ).count()

    @property
    def estimated_total_minutes(self):
        result = self.advertisements.aggregate(
            total=models.Sum(
                "outlet__estimated_submission_minutes"
            )
        )

        return result["total"] or 0

    @property
    def estimated_remaining_minutes(self):
        completed_statuses = [
            EventAdvertisement.Status.PUBLISHED,
            EventAdvertisement.Status.SKIPPED,
            EventAdvertisement.Status.NOT_APPLICABLE,
        ]

        result = (
            self.advertisements
            .exclude(status__in=completed_statuses)
            .aggregate(
                total=models.Sum(
                    "outlet__estimated_submission_minutes"
                )
            )
        )

        return result["total"] or 0

    playbook = models.ForeignKey(
        "AdvertisingPlaybook",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="campaigns",
        help_text="Optional reusable copy and submission guidance for this campaign.",
    )

    advertising_title = models.CharField(
        max_length=250,
        blank=True,
    )

    short_description = models.TextField(
        blank=True,
    )

    long_description = models.TextField(
        blank=True,
    )

    facebook_copy = models.TextField(
        blank=True,
    )

    newsletter_copy = models.TextField(
        blank=True,
    )

    community_calendar_copy = models.TextField(
        blank=True,
    )

    email_copy = models.TextField(
        blank=True,
    )

    image_guidance = models.TextField(
        blank=True,
    )

    copy_generated_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"Advertising Campaign: {self.event.event_name}"


class EventAdvertisement(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "NOT_STARTED", "Not Started"
        READY = "READY", "Ready to Submit"
        SUBMITTED = "SUBMITTED", "Submitted"
        WAITING_APPROVAL = "WAITING_APPROVAL", "Waiting for Approval"
        PUBLISHED = "PUBLISHED", "Published"
        REJECTED = "REJECTED", "Rejected"
        SKIPPED = "SKIPPED", "Skipped"
        NOT_APPLICABLE = "NOT_APPLICABLE", "Not Applicable"
        MISSED_DEADLINE = "MISSED_DEADLINE", "Missed Deadline"
        EXPIRED = "EXPIRED", "Expired"

    campaign = models.ForeignKey(
        AdvertisingCampaign,
        on_delete=models.CASCADE,
        related_name="advertisements",
    )

    outlet = models.ForeignKey(
        AdvertisingOutlet,
        on_delete=models.PROTECT,
        related_name="event_advertisements",
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.NOT_STARTED,
    )

    submission_deadline = models.DateField(
        null=True,
        blank=True,
    )

    # ---------------------------------------------------------
    # Outlet-specific generated copy
    # ---------------------------------------------------------

    generated_title = models.CharField(
        max_length=500,
        blank=True,
        help_text="Event title prepared specifically for this outlet.",
    )

    generated_description = models.TextField(
        blank=True,
        help_text="Event description prepared specifically for this outlet.",
    )

    generated_email_subject = models.CharField(
        max_length=500,
        blank=True,
        help_text=(
            "Email subject prepared for outlets that accept submissions by email."
        ),
    )

    generated_email_body = models.TextField(
        blank=True,
        help_text=(
            "Email body prepared for outlets that accept submissions by email."
        ),
    )

    copy_generated_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    copy_reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    copy_reviewed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_event_advertisements",
    )

    # ---------------------------------------------------------
    # Final submitted copy
    # ---------------------------------------------------------

    submitted_title = models.CharField(
        max_length=500,
        blank=True,
        help_text="The final title actually submitted to the outlet.",
    )

    submitted_description = models.TextField(
        blank=True,
        help_text="The final description actually submitted to the outlet.",
    )

    submitted_email_subject = models.CharField(
        max_length=500,
        blank=True,
        help_text="The final email subject actually sent to the outlet.",
    )

    submitted_email_body = models.TextField(
        blank=True,
        help_text="The final email body actually sent to the outlet.",
    )

    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    submitted_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="submitted_event_advertisements",
    )

    published_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    published_url = models.URLField(blank=True)

    external_reference = models.CharField(
        max_length=200,
        blank=True,
        help_text="Confirmation number, post ID, or other external reference.",
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [
            "submission_deadline",
            "outlet__priority",
            "outlet__name",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["campaign", "outlet"],
                name="unique_campaign_advertising_outlet",
            )
        ]

        verbose_name = "Event Advertisement"
        verbose_name_plural = "Event Advertisements"

    def __str__(self):
        return f"{self.campaign.event.event_name} — {self.outlet.name}"

class AdvertisingPlaybook(models.Model):
    class Voice(models.TextChoices):
        FRIENDLY = "FRIENDLY", "Friendly"
        EDUCATIONAL = "EDUCATIONAL", "Educational"
        PROFESSIONAL = "PROFESSIONAL", "Professional"
        EXCITING = "EXCITING", "Exciting"
        FORMAL = "FORMAL", "Formal"

    class Audience(models.TextChoices):
        GENERAL_PUBLIC = "GENERAL_PUBLIC", "General Public"
        FAMILIES = "FAMILIES", "Families"
        BEGINNERS = "BEGINNERS", "Beginners"
        STUDENTS = "STUDENTS", "Students"
        SCOUTS = "SCOUTS", "Scouts"
        CAMPERS = "CAMPERS", "Campers"
        EDUCATORS = "EDUCATORS", "Educators"
        ASTRONOMERS = "ASTRONOMERS", "Experienced Astronomers"

    name = models.CharField(
        max_length=150,
        unique=True,
    )

    description = models.TextField(
        blank=True,
        help_text=(
            "Internal description of when this playbook should be used."
        ),
    )

    voice = models.CharField(
        max_length=20,
        choices=Voice.choices,
        default=Voice.FRIENDLY,
        help_text="Overall tone used when generating advertising copy.",
    )

    target_audience = models.CharField(
        max_length=25,
        choices=Audience.choices,
        default=Audience.GENERAL_PUBLIC,
        help_text="Primary audience this advertising is intended for.",
    )

    key_messages = models.TextField(
        blank=True,
        help_text=(
            "Important ideas that should always appear in generated advertising."
        ),
    )

    avoid_language = models.TextField(
        blank=True,
        help_text=(
            "Words, phrases, or topics that should be avoided."
        ),
    )

    short_description_template = models.TextField(
        blank=True,
        help_text=(
            "Optional short promotional template.\n\n"
            "Available placeholders:\n"
            "{event_name}\n"
            "{event_date}\n"
            "{start_time}\n"
            "{end_time}\n"
            "{location_name}\n"
            "{partner_name}\n"
            "{city}"
        ),
    )

    long_description_template = models.TextField(
        blank=True,
        help_text="Optional long-form advertising template.",
    )

    facebook_template = models.TextField(
        blank=True,
        help_text="Optional Facebook-specific template.",
    )

    newsletter_template = models.TextField(
        blank=True,
        help_text="Optional newsletter template.",
    )

    community_calendar_template = models.TextField(
        blank=True,
        help_text="Optional community calendar template.",
    )

    email_template = models.TextField(
        blank=True,
        help_text="Optional email announcement template.",
    )

    generate_facebook_copy = models.BooleanField(
        default=True,
    )

    generate_newsletter_copy = models.BooleanField(
        default=True,
    )

    generate_calendar_copy = models.BooleanField(
        default=True,
    )

    generate_email_copy = models.BooleanField(
        default=True,
    )

    image_guidance = models.TextField(
        blank=True,
        help_text=(
            "Suggested image style or subject to accompany generated advertisements."
        ),
    )

    automation_notes = models.TextField(
        blank=True,
        help_text=(
            "Internal notes used by browser-assisted advertising automation."
        ),
    )

    active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Advertising Playbook"
        verbose_name_plural = "Advertising Playbooks"

    def __str__(self):
        return self.name

class PartnerLocationResource(models.Model):
    partner = models.ForeignKey(
        Partner,
        on_delete=models.CASCADE,
        related_name="location_resources",
    )

    file = models.FileField(
        upload_to="partner_location_resources/",
    )

    caption = models.CharField(
        max_length=255,
        blank=True,
    )

    sort_order = models.PositiveIntegerField(
        default=0,
    )

    active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = (
            "sort_order",
            "id",
        )

    def __str__(self):
        if self.caption:
            return f"{self.partner} — {self.caption}"

        return f"{self.partner} — Location Resource"

    @property
    def is_image(self):
        if not self.file:
            return False

        filename = self.file.name.lower()

        return filename.endswith(
            (
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".webp",
            )
        )

    @property
    def is_pdf(self):
        if not self.file:
            return False

        return self.file.name.lower().endswith(".pdf")