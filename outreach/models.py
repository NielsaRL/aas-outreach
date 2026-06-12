from django.db import models
from datetime import datetime
from .services.astronomy import calculate_twilight_times, calculate_moon_info
from django.core.exceptions import ValidationError
from multiselectfield import MultiSelectField


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
        editable=False,
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
    volunteer_name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    equipment_owned = models.TextField(blank=True, help_text="List equipment this volunteer owns, one item per line.")
    active = models.BooleanField(default=True)
    host_trained = models.BooleanField(
    default=False,
    help_text="Check if this volunteer is trained to host events."
    )

    cleared_by_pfsp = models.BooleanField(
        default=False,
        help_text="Check if this volunteer is cleared by PFSP."
    )
    notes = models.TextField(blank=True)

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

        if self.status == "CONFIRMED":
            EventLog.objects.get_or_create(event=self)

    def __str__(self):
        return self.event_name
    
class EventVolunteer(models.Model):

    ROLE_CHOICES = [
        ("HOST", "Host"),
        ("TELESCOPE", "Telescope Operator"),
        ("WELCOME", "Welcome Table"),
        ("ZOO", "Telescope Petting Zoo"),
        ("DISPLAY", "Display Setup"),
        ("OTHER", "Other"),
    ]

    event = models.ForeignKey(ScheduledEvent, on_delete=models.CASCADE, related_name="event_volunteers")
    volunteer = models.ForeignKey(Volunteer, on_delete=models.CASCADE, related_name="event_assignments")

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="TELESCOPE"
    )

    notes = models.TextField(blank=True)

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