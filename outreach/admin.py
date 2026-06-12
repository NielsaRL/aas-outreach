from django.contrib import admin
from django import forms
from .services.targets import suggest_targets_for_event
from .services.weather import update_weather_for_event
from django.contrib import messages
from django.utils.html import format_html
from .models import Partner, Volunteer, ScheduledEvent, EventVolunteer, EventLog, AstronomicalTarget, EventTarget, SuggestedEvent, SchedulerRun

class EventVolunteerInlineForm(forms.ModelForm):
    class Meta:
        model = EventVolunteer
        fields = "__all__"
        widgets = {
            "notes": forms.Textarea(
                attrs={
                    "rows": 1,
                    "cols": 20,
                }
            ),
        }

class EventVolunteerInline(admin.TabularInline):
    model = EventVolunteer
    form = EventVolunteerInlineForm
    extra = 5
    autocomplete_fields = ("volunteer",)

    fields = (
        "volunteer",
        "role",
        "notes",
    )

class EventLogInline(admin.StackedInline):
    model = EventLog
    extra = 0
    max_num = 1

class EventTargetInlineForm(forms.ModelForm):
    class Meta:
        model = EventTarget
        fields = "__all__"
        widgets = {
            "notes": forms.Textarea(
                attrs={
                    "rows": 1,
                    "cols": 30,
                }
            ),
        }

class EventTargetInline(admin.TabularInline):
    model = EventTarget
    form = EventTargetInlineForm
    extra = 3
    autocomplete_fields = ("target",)

    fields = (
        "target",
        "can_observe_during_event",
        "good_talking_point",
        "altitude_degrees",
        "azimuth_degrees",
        "visible_start_time",
        "visible_end_time",
        "notes",
    )


    readonly_fields = (
        "altitude_degrees",
        "azimuth_degrees",
        "visible_start_time",
        "visible_end_time",
    )

@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = (
        "partner_name",
        "sky_brightness_sqm",
        "auto_bortle_class",
        "partner_type",
        "scheduling_type",
        "priority",
        "events_per_year",
        "allowed_weekdays",
        "allowed_weekday_occurrences",
        "allowed_months",
        "minimum_event_duration_minutes",
        "maximum_event_duration_minutes",
        "must_leave_by",
        "location_name",
        "contact_name",
        "active",
    )

    list_filter = (
        "partner_type",
        "scheduling_type",
        "priority",
        "allowed_weekdays",
        "allowed_weekday_occurrences",
        "allowed_months",
        "active",
    )

    search_fields = (
        "partner_name",
        "location_name",
        "address",
        "contact_name",
        "contact_email",
        "contact_phone",
        "notes",
    )

    readonly_fields = (
        "sky_brightness_sqm",
        "auto_bortle_class",
    )

@admin.register(Volunteer)
class VolunteerAdmin(admin.ModelAdmin):
    list_display = (
        "volunteer_name",
        "email",
        "phone",
        "host_trained",
        "cleared_by_pfsp",
        "active",
    )

    list_filter = (
        "host_trained",
        "cleared_by_pfsp",
        "active",
    )

    search_fields = (
        "volunteer_name",
        "email",
    )

@admin.register(ScheduledEvent)
class ScheduledEventAdmin(admin.ModelAdmin):
    list_display = (
        "event_name",
        "partner",
        "event_date",
        "status",
        "date_confirmed",
        "host_display",
        "night_sky_chart_link",
        "weather_heat_index_f",
        "weather_temperature_f",
        "weather_wind_speed_mph",
        "weather_precipitation_probability",
        "weather_cloud_cover_percent",
        "weather_rain_text",
        "weather_thunder_text",
        "weather_watch_text",
        "weather_warning_text",
        "weather_summary",
        "weather_last_checked",
    )

    list_filter = (
        "status",
        "date_confirmed",
        "event_title_type",
        "event_date",
        ("partner", admin.RelatedOnlyFieldListFilter),
        ("host", admin.RelatedOnlyFieldListFilter),
    )

    search_fields = (
        "event_name",
        "partner__partner_name",
        "partner__location_name",
        "manual_host_name",
        "notes",
    )

    autocomplete_fields = (
        "partner",
        "host",
    )

    date_hierarchy = "event_date"

    readonly_fields = (
        "event_name",
        "night_sky_chart_link",
        "sunset_time",
        "civil_dusk_time",
        "nautical_dusk_time",
        "moon_illumination",
        "moon_phase",
        "suggested_talk_start_time",
        "suggested_laser_tour_time",
    )

    actions = (
        "suggest_targets",
        "update_weather",
    )
    
    @admin.action(description="Suggest targets and talking points")
    def suggest_targets(self, request, queryset):
        total_added = 0

        for event in queryset:
            targets = suggest_targets_for_event(event)
            total_added += len(targets)

        self.message_user(
            request,
            f"{total_added} target suggestion(s) added.",
            messages.SUCCESS,
        )

    @admin.action(description="Update weather forecast")
    def update_weather(self, request, queryset):
        updated_count = 0
        failed_count = 0

        for event in queryset:
            updated = update_weather_for_event(event)

            if updated:
                updated_count += 1
            else:
                failed_count += 1

        self.message_user(
            request,
            f"{updated_count} event(s) updated. {failed_count} event(s) had no forecast.",
            messages.SUCCESS,
        )

    inlines = [EventVolunteerInline, EventTargetInline, EventLogInline]

    def night_sky_chart_link(self, obj):
        if not obj.event_date:
            return ""

        url = (
            "https://in-the-sky.org/skymap2.php?"
            f"day={obj.event_date.day}"
            f"&month={obj.event_date.month}"
            f"&year={obj.event_date.year}"
            "&town=4671654"
        )

        return format_html(
            '<a href="{}" target="_blank">Night sky chart</a>',
            url,
        )

    night_sky_chart_link.short_description = "Sky Chart"

@admin.register(AstronomicalTarget)
class AstronomicalTargetAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "target_type",
        "constellation",
        "best_months",
        "visible_during_event",
        "discussion_only",
        "active",
    )

    list_filter = (
        "target_type",
        "visible_during_event",
        "discussion_only",
        "active",
    )

    search_fields = (
        "name",
        "constellation",
        "outreach_notes",
    )

@admin.register(SuggestedEvent)
class SuggestedEventAdmin(admin.ModelAdmin):
    list_display = (
        "partner",
        "scheduler_run",
        "suggested_date",
        "sunset_time",
        "start_time",
        "end_time",
        "status",
        "manual_entry",
        "created_at",
    )

    list_filter = (
        "status",
        "manual_entry",
        "scheduler_run",
        "suggested_date",
        ("partner", admin.RelatedOnlyFieldListFilter),
    )

    search_fields = (
        "partner__partner_name",
        "partner__location_name",
        "rejection_reason",
    )

    date_hierarchy = "suggested_date"

    readonly_fields = (
        "sunset_time",
        "start_time",
        "end_time",
        "created_at",
    )

    actions = (
        "approve_suggestions",
        "reject_suggestions",
    )

    @admin.action(description="Approve selected suggestions and create scheduled events")
    def approve_suggestions(self, request, queryset):
        created_count = 0
        updated_count = 0
        approved_count = 0

        for suggestion in queryset:
            existing_event = ScheduledEvent.objects.filter(
                partner=suggestion.partner,
                event_date=suggestion.suggested_date,
            ).first()

            if existing_event:
                existing_event.event_title_type = "STAR_PARTY"
                existing_event.start_time = suggestion.start_time
                existing_event.end_time = suggestion.end_time
                existing_event.status = "PLANNED"
                existing_event.save()

                updated_count += 1

            else:
                ScheduledEvent.objects.create(
                    partner=suggestion.partner,
                    event_date=suggestion.suggested_date,
                    event_title_type="STAR_PARTY",
                    start_time=suggestion.start_time,
                    end_time=suggestion.end_time,
                    status="PLANNED",
                )

                created_count += 1

            suggestion.status = "APPROVED"
            suggestion.save()
            approved_count += 1

        self.message_user(
            request,
            (
                f"{approved_count} suggestion(s) approved. "
                f"{created_count} scheduled event(s) created. "
                f"{updated_count} existing event(s) updated."
            ),
            messages.SUCCESS,
        )

    @admin.action(description="Reject selected suggestions")
    def reject_suggestions(self, request, queryset):
        updated = queryset.update(status="REJECTED")

        self.message_user(
            request,
            f"{updated} suggestion(s) rejected.",
            messages.WARNING,
        )

@admin.register(SchedulerRun)
class SchedulerRunAdmin(admin.ModelAdmin):
    list_display = (
        "start_date",
        "end_date",
        "created_at",
    )

    readonly_fields = (
        "created_at",
    )