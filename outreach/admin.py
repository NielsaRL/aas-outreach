from django.contrib import admin, messages
from django import forms
from .services.astronomy import calculate_moon_info
from .services.targets import suggest_targets_for_event
from .services.weather import update_weather_for_event
from .services.star_chart import generate_star_chart_pdf
from outreach.services.advertising_copy import generate_campaign_copy
from .services.advertising import generate_advertising_campaign
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpRequest, HttpResponse
import csv

from django.utils.dateparse import parse_date
from datetime import date, timedelta
import calendar
from .models import EventChecklist, Partner, Volunteer, ScheduledEvent, BlackoutDate, EventVolunteer, EventLog, AstronomicalTarget, EventTarget, SuggestedEvent, SchedulerRun, EventChecklistItem, AdvertisingOutlet, AdvertisingCampaign, EventAdvertisement, AdvertisingPlaybook

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
        "pfsp_status",
        "role",
        "telescope_count",
        "notes",
    )

    readonly_fields = (
        "pfsp_status",
    )

    @admin.display(description="PFSP")
    def pfsp_status(self, obj):
        if not obj or not obj.volunteer_id:
            return "—"

        if obj.volunteer.cleared_by_pfsp:
            return format_html(
                '<span style="'
                'display:inline-block;'
                'padding:3px 8px;'
                'border-radius:10px;'
                'background:#d1e7dd;'
                'color:#0f5132;'
                'font-weight:600;'
                '">{}</span>',
                "✓ PFSP",
            )

        return format_html(
            '<span style="'
            'display:inline-block;'
            'padding:3px 8px;'
            'border-radius:10px;'
            'background:#f2f2f2;'
            'color:#777;'
            '">{}</span>',
            "Not PFSP",
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

class EventChecklistItemInlineForm(forms.ModelForm):
    class Meta:
        model = EventChecklistItem
        fields = "__all__"
        
        widgets = {
            "notes": forms.Textarea(
                attrs={
                    "rows": 1,
                    "cols": 40,
                }
            ),
        }
class EventChecklistItemInline(admin.TabularInline):
    model = EventChecklistItem
    form = EventChecklistItemInlineForm
    extra = 0
    show_change_link = False
    ordering = ("due_date", "title")    

    fields = (
        "title",
        "due_date",
        "status",
        "cancellation_item",
        "notes",
    )

    readonly_fields = (
        "title",
        "due_date",
        "cancellation_item",
    )

class EventAdvertisementInlineForm(forms.ModelForm):
    class Meta:
        model = EventAdvertisement
        fields = "__all__"
        widgets = {
            "notes": forms.Textarea(
                attrs={
                    "rows": 1,
                    "cols": 40,
                }
            ),
        }


class EventAdvertisementInline(admin.TabularInline):
    model = EventAdvertisement
    form = EventAdvertisementInlineForm
    extra = 0
    autocomplete_fields = ("outlet",)
    ordering = (
        "submission_deadline",
        "outlet__priority",
        "outlet__name",
    )
    fields = (
        "outlet",
        "submission_deadline",
        "status",
        "submitted_at",
        "submitted_by",
        "published_url",
        "notes",
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

    fieldsets = (
        ("Basic Information", {
            "fields": (
                "partner_name",
                "partner_type",
                "scheduling_type",
                "priority",
                "active",
            )
        }),
        ("Scheduling Rules", {
            "fields": (
                "events_per_year",
                "allowed_weekdays",
                "allowed_weekday_occurrences",
                "allowed_months",
                "minimum_event_duration_minutes",
                "maximum_event_duration_minutes",
                "must_leave_by",
            )
        }),
        ("Location", {
            "fields": (
                "location_name",
                "address",
                "latitude",
                "longitude",
                "sky_brightness_sqm",
                "auto_bortle_class",
            )
        }),
        ("Contact", {
            "fields": (
                "contact_name",
                "contact_email",
                "contact_phone",
            )
        }),
        ("Volunteer Location Instructions", {
            "fields": (
                "volunteer_arrival_instructions",
                "meeting_location",
                "parking_instructions",
                "setup_location_notes",
            )
        }),
        ("General Notes", {
            "fields": (
                "notes",
            )
        }),
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

    readonly_fields = ("auto_bortle_class",)

    ordering = ("partner_name",)
    

@admin.register(Volunteer)
class VolunteerAdmin(admin.ModelAdmin):
    list_display = (
        "volunteer_name",
        "email",
        "phone",
        "host_trained",
        "outreach_committee",
        "cleared_by_pfsp",
        "active",
    )

    list_filter = (
        "host_trained",
        "outreach_committee",
        "cleared_by_pfsp",
        "active",
    )

    search_fields = ("first_name", "last_name", "email")

    ordering = ("last_name", "first_name")

@admin.register(ScheduledEvent)
class ScheduledEventAdmin(admin.ModelAdmin):
    list_display = (
        "event_name",
        "partner",
        "event_date",
        "status",
        "advertising_radius_miles",
        "advertise_to_full_service_area",
        "advertising_campaign_link",
        "advertising_progress",
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

    ordering = ("event_date", "start_time")

    date_hierarchy = "event_date"

    readonly_fields = (
        "event_name",
        "advertising_campaign_link",
        "advertising_progress",
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
        "generate_star_charts",
        "generate_advertising_campaigns",
        "export_volunteer_roster",
    )

    @admin.register(BlackoutDate)
    class BlackoutDateAdmin(admin.ModelAdmin):
        list_display = (
            "blackout_date",
            "reason",
            "active",
        )

        list_filter = (
            "active",
        )

        search_fields = (
            "reason",
        )

        ordering = (
            "blackout_date",
        )

        change_list_template = "admin/outreach/blackoutdate/change_list.html"

        def get_urls(self):
            urls = super().get_urls()

            custom_urls = [
                path(
                    "bulk-add/",
                    self.admin_site.admin_view(self.bulk_add_view),
                    name="outreach_blackoutdate_bulk_add",
                ),
            ]

            return custom_urls + urls

        def bulk_add_view(self, request):
            if request.method == "POST":
                blackout_text = request.POST.get("blackout_dates", "").strip()

                created_count = 0
                skipped_count = 0
                error_lines = []

                for line_number, raw_line in enumerate(
                    blackout_text.splitlines(),
                    start=1,
                ):
                    line = raw_line.strip()

                    if not line:
                        continue

                    if "|" not in line:
                        error_lines.append(
                            f"Line {line_number}: missing | separator."
                        )
                        continue

                    date_text, reason = line.split("|", 1)

                    date_text = date_text.strip()
                    reason = reason.strip()

                    try:
                        blackout_date = datetime.strptime(
                            date_text,
                            "%Y-%m-%d",
                        ).date()
                    except ValueError:
                        error_lines.append(
                            f"Line {line_number}: invalid date '{date_text}'. "
                            "Use YYYY-MM-DD."
                        )
                        continue

                    if not reason:
                        error_lines.append(
                            f"Line {line_number}: reason is required."
                        )
                        continue

                    blackout, created = BlackoutDate.objects.get_or_create(
                        blackout_date=blackout_date,
                        defaults={
                            "reason": reason,
                            "active": True,
                        },
                    )

                    if created:
                        created_count += 1
                    else:
                        skipped_count += 1

                if created_count:
                    self.message_user(
                        request,
                        f"{created_count} blackout date(s) added.",
                        messages.SUCCESS,
                    )

                if skipped_count:
                    self.message_user(
                        request,
                        f"{skipped_count} existing blackout date(s) skipped.",
                        messages.WARNING,
                    )

                if error_lines:
                    self.message_user(
                        request,
                        " ".join(error_lines),
                        messages.ERROR,
                    )

                if not error_lines:
                    return redirect(
                        "admin:outreach_blackoutdate_changelist"
                    )

            context = {
                **self.admin_site.each_context(request),
                "title": "Bulk Add Blackout Dates",
            }

            return render(
                request,
                "admin/outreach/blackoutdate/bulk_add.html",
                context,
            )
    
    @admin.action(description="Generate advertising campaigns")
    def generate_advertising_campaigns(self, request, queryset):
        campaign_count = 0
        created_task_count = 0
        existing_task_count = 0
        skipped_deadline_count = 0
        skipped_radius_count = 0
        skipped_missing_city_count = 0
        skipped_event_type_count = 0
        skipped_missing_coordinates_count = 0

        for event in queryset.select_related("partner"):
            result = generate_advertising_campaign(
                event=event,
                generated_by=request.user,
            )

            if result.campaign_created:
                campaign_count += 1

            created_task_count += result.advertisements_created
            existing_task_count += result.advertisements_existing
            skipped_deadline_count += (
                result.outlets_skipped_deadline
            )
            skipped_radius_count += (
                result.outlets_skipped_radius
            )
            skipped_missing_city_count += (
                result.outlets_skipped_missing_city
            )
            skipped_event_type_count += (
                result.outlets_skipped_event_type
            )
            skipped_missing_coordinates_count += (
                result.outlets_skipped_missing_venue_coordinates
            )

        self.message_user(
            request,
            (
                f"{campaign_count} new campaign(s) created. "
                f"{created_task_count} task(s) added. "
                f"{existing_task_count} existing task(s) preserved. "
                f"{skipped_deadline_count} skipped because the "
                f"submission deadline passed. "
                f"{skipped_radius_count} skipped because they were "
                f"outside the campaign radius. "
                f"{skipped_missing_city_count} skipped because their "
                f"city was not in the city lookup. "
                f"{skipped_event_type_count} skipped because they do "
                f"not accept the event type. "
                f"{skipped_missing_coordinates_count} skipped because "
                f"venue coordinates were unavailable."
            ),
            messages.SUCCESS,
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

    @admin.action(description="Generate star chart PDF")
    def generate_star_charts(self, request, queryset):
        generated_count = 0

        for event in queryset:
            generate_star_chart_pdf(event)
            generated_count += 1

        self.message_user(
            request,
            f"{generated_count} star chart PDF(s) generated.",
            messages.SUCCESS,
        )

    @admin.action(description="Download volunteer roster")
    def export_volunteer_roster(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(
                request,
                "Please select exactly one event to download its volunteer roster.",
                messages.WARNING,
            )
            return None

        event = queryset.first()

        volunteers = (
            EventVolunteer.objects
            .filter(event=event)
            .select_related("volunteer")
            .order_by(
                "volunteer__last_name",
                "volunteer__first_name",
            )
        )

        filename = (
            f"volunteer_roster_"
            f"{event.event_date}_"
            f"event_{event.id}.csv"
        )

        response = HttpResponse(
            content_type="text/csv"
        )

        response["Content-Disposition"] = (
            f'attachment; filename="{filename}"'
        )

        writer = csv.writer(response)

        writer.writerow(
            [
                "Volunteer",
                "First Name",
                "Last Name",
                "Email",
                "Phone",
                "Role",
                "Telescopes",
                "PFSP Approved",
                "Notes",
            ]
        )

        for assignment in volunteers:
            volunteer = assignment.volunteer

            writer.writerow(
                [
                    volunteer.volunteer_name,
                    volunteer.first_name,
                    volunteer.last_name,
                    volunteer.email,
                    volunteer.phone,
                    assignment.get_role_display(),
                    assignment.telescope_count,
                    "Yes" if volunteer.cleared_by_pfsp else "No",
                    assignment.notes,
                ]
            )

        return response

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

    def advertising_campaign_link(self, obj):
        if not obj or not obj.pk:
            return "Save the event before generating a campaign."

        try:
            campaign = obj.advertising_campaign
        except AdvertisingCampaign.DoesNotExist:
            generate_url = reverse(
                "admin:outreach_scheduledevent_generate_advertising",
                args=[obj.pk],
            )

            return format_html(
                '<a class="button" href="{}">Generate campaign</a>',
                generate_url,
            )

        campaign_url = reverse(
            "admin:outreach_advertisingcampaign_change",
            args=[campaign.pk],
        )

        return format_html(
            '<a href="{}">Open campaign</a>',
            campaign_url,
        )

    advertising_campaign_link.short_description = "Advertising Campaign"


    def advertising_progress(self, obj):
        if not obj or not obj.pk:
            return ""

        try:
            campaign = obj.advertising_campaign
        except AdvertisingCampaign.DoesNotExist:
            return "Not generated"

        return (
            f"{campaign.completed_outlets}/"
            f"{campaign.total_outlets} complete "
            f"({campaign.progress_percent}%)"
        )

    advertising_progress.short_description = "Advertising Progress"

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
    change_list_template = "admin/outreach/scheduledevent/change_list.html"

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                "calendar/",
                self.admin_site.admin_view(self.calendar_view),
                name="outreach_scheduledevent_calendar",
            ),
            path(
                "<int:event_id>/generate-advertising/",
                self.admin_site.admin_view(
                    self.generate_advertising_campaign_view
                ),
                name="outreach_scheduledevent_generate_advertising",
            ),
        ]

        return custom_urls + urls

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        return queryset.select_related(
            "partner",
            "host",
        ).prefetch_related(
            "advertising_campaign__advertisements",
        )

    def generate_advertising_campaign_view(self, request, event_id):
        event = self.get_object(request, event_id)

        if event is None:
            self.message_user(
                request,
                "The scheduled event could not be found.",
                messages.ERROR,
            )

            return HttpResponseRedirect(
                reverse("admin:outreach_scheduledevent_changelist")
            )

        result = generate_advertising_campaign(
            event=event,
            generated_by=request.user,
        )

        if result.campaign_created:
            campaign_message = "Advertising campaign created."
        else:
            campaign_message = "Existing advertising campaign updated."

        self.message_user(
            request,
            (
                f"{campaign_message} "
                f"{result.advertisements_created} task(s) added and "
                f"{result.advertisements_existing} existing task(s) "
                f"preserved. "
                f"{result.outlets_skipped_deadline} outlet(s) skipped "
                f"because their deadlines passed. "
                f"{result.outlets_skipped_radius} outlet(s) skipped "
                f"because they were outside the selected radius. "
                f"{result.outlets_skipped_missing_city} outlet(s) skipped "
                f"because their city was not found in the lookup."
            ),
            messages.SUCCESS,
        )

        campaign_url = reverse(
            "admin:outreach_advertisingcampaign_change",
            args=[result.campaign.pk],
        )

        return HttpResponseRedirect(campaign_url)

    def calendar_view(self, request):
        today = date.today()
        year = int(request.GET.get("year", today.year))
        month = int(request.GET.get("month", today.month))

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
            .select_related(
                "partner",
                "host",
            )
            .order_by(
                "event_date",
                "start_time",
            )
        )

        events_by_date = {}

        for event in events:
            event.admin_url = reverse(
                "admin:outreach_scheduledevent_change",
                args=[event.pk],
            )

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

                moon_color = (
                    round(65 + ((illumination / 100) * 175)),
                    round(67 + ((illumination / 100) * 175)),
                    round(130 + ((illumination / 100) * 125)),
                )

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
                        "moon_color": moon_color,
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

        context = {
            **self.admin_site.each_context(request),
            "title": "Scheduled Events Calendar",
            "year": year,
            "month": month,
            "month_name": calendar.month_name[month],
            "weeks": weeks,
            "previous_year": previous_year,
            "previous_month": previous_month,
            "next_year": next_year,
            "next_month": next_month,
        }

        return render(
            request,
            "admin/outreach/scheduledevent/calendar.html",
            context,
        )

@admin.register(AstronomicalTarget)
class AstronomicalTargetAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "target_type",
        "constellation",
        "best_months_display",
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

    ordering = ("name",)

    def best_months_display(self, obj):
        if not obj.best_months:
            return ""

        month_names = {
            "1": "Jan",
            "2": "Feb",
            "3": "Mar",
            "4": "Apr",
            "5": "May",
            "6": "Jun",
            "7": "Jul",
            "8": "Aug",
            "9": "Sep",
            "10": "Oct",
            "11": "Nov",
            "12": "Dec",
        }

        return ", ".join(
            month_names.get(str(month), str(month))
            for month in obj.best_months
        )

    best_months_display.short_description = "Best Months"

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

    ordering = ("suggested_date", "start_time")

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

class EventChecklistDateFilter(admin.SimpleListFilter):
    title = "Event Date"
    parameter_name = "event_date_range"

    def lookups(self, request, model_admin):
        return (
            ("upcoming", "Upcoming"),
            ("all", "All"),
        )

    def queryset(self, request, queryset):
        today = date.today()

        if self.value() == "all":
            return queryset

        return queryset.filter(event_date__gte=today)

    def choices(self, changelist):
        for lookup, title in self.lookup_choices:
            yield {
                "selected": (
                    self.value() == lookup
                    or (
                        self.value() is None
                        and lookup == "upcoming"
                    )
                ),
                "query_string": changelist.get_query_string(
                    {self.parameter_name: lookup},
                    [],
                ),
                "display": title,
            }


@admin.register(EventChecklist)
class EventChecklistAdmin(admin.ModelAdmin):
    list_display = (
        "event_name",
        "event_date",
        "partner",
        "status",
        "checklist_progress",
    )

    list_filter = (
        EventChecklistDateFilter,
    )

    fields = (
        "event_name",
        "event_date",
        "partner",
        "status",
    )

    readonly_fields = (
        "event_name",
        "event_date",
        "partner",
        "status",
    )

    ordering = ("event_date", "start_time")

    inlines = [EventChecklistItemInline]

    def checklist_progress(self, obj):
        total = obj.checklist_items.count()

        if total == 0:
            return "No checklist"

        complete = obj.checklist_items.filter(
            status__in=["DONE", "NA"]
        ).count()

        return f"{complete}/{total} complete"

    checklist_progress.short_description = "Checklist Progress"

@admin.register(AdvertisingOutlet)
class AdvertisingOutletAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "submission_method",
        "priority",
        "city",
        "county",
        "minimum_lead_days",
        "estimated_submission_minutes",
        "maximum_description_characters",
        "covers_full_service_area",
        "active",
    )

    list_filter = (
        "active",
        "category",
        "submission_method",
        "priority",
        "state",
        "covers_full_service_area",
        "requires_account",
        "requires_image",
        "requires_approval",
        "requires_captcha",
        "allows_images",
        "allows_links",
        "allows_html",
        "allows_emojis",
        "allows_hashtags",
        "requires_plain_text",
        "accepts_star_parties",
        "accepts_solar_outreach",
        "accepts_library_programs",
        "accepts_sidewalk_astronomy",
        "accepts_custom_events",
    )

    search_fields = (
        "name",
        "city",
        "county",
        "state",
        "contact_name",
        "contact_email",
        "website_url",
        "submission_url",
        "submission_instructions",
        "content_guidance",
        "verification_notes",
        "notes",
    )

    ordering = (
        "priority",
        "name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "name",
                    "category",
                    "submission_method",
                    "priority",
                    "active",
                )
            },
        ),
        (
            "Web and Contact Information",
            {
                "fields": (
                    "website_url",
                    "submission_url",
                    "contact_name",
                    "contact_email",
                    "contact_phone",
                )
            },
        ),
        (
            "Geographic Coverage",
            {
                "fields": (
                    "city",
                    "county",
                    "state",
                    "service_radius_miles",
                    "covers_full_service_area",
                )
            },
        ),
        (
            "Submission Timing",
            {
                "fields": (
                    "minimum_lead_days",
                    "preferred_lead_days",
                    "estimated_submission_minutes",
                )
            },
        ),
        (
            "Accepted Event Types",
            {
                "fields": (
                    "accepts_star_parties",
                    "accepts_solar_outreach",
                    "accepts_library_programs",
                    "accepts_sidewalk_astronomy",
                    "accepts_custom_events",
                )
            },
        ),
        (
            "General Submission Requirements",
            {
                "fields": (
                    "requires_account",
                    "requires_image",
                    "requires_approval",
                    "requires_captcha",
                )
            },
        ),
        (
            "Required Event Information",
            {
                "fields": (
                    "requires_event_title",
                    "requires_description",
                    "requires_start_time",
                    "requires_end_time",
                    "requires_address",
                    "requires_cost",
                    "requires_contact_email",
                    "requires_contact_phone",
                    "requires_registration_url",
                )
            },
        ),
        (
            "Content Limits",
            {
                "fields": (
                    "maximum_title_characters",
                    "maximum_description_characters",
                )
            },
        ),
        (
            "Content Formatting",
            {
                "fields": (
                    "allows_images",
                    "allows_links",
                    "allows_html",
                    "allows_emojis",
                    "allows_hashtags",
                    "requires_plain_text",
                    "content_guidance",
                )
            },
        ),
        (
            "Submission Instructions",
            {
                "fields": (
                    "submission_instructions",
                    "notes",
                )
            },
        ),
        (
            "Verification",
            {
                "fields": (
                    "last_verified_at",
                    "verification_notes",
                ),
                "classes": (
                    "collapse",
                ),
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": (
                    "collapse",
                ),
            },
        ),
    )

@admin.register(AdvertisingCampaign)
class AdvertisingCampaignAdmin(admin.ModelAdmin):
    change_form_template = (
        "admin/outreach/advertisingcampaign/change_form.html"
    )

    list_display = (
        "event",
        "status",
        "campaign_progress",
        "estimated_time_remaining",
        "generated_at",
        "generated_by",
        "last_regenerated_at",
    )

    list_filter = (
        "status",
        "generated_at",
        "last_regenerated_at",
        "event__event_title_type",
        "event__status",
    )

    search_fields = (
        "event__event_name",
        "event__partner__partner_name",
        "event__partner__location_name",
        "notes",
    )

    autocomplete_fields = (
        "event",
        "playbook",
        "generated_by",
    )

    readonly_fields = (
        "generated_at",
        "last_regenerated_at",
        "copy_generated_at",
        "campaign_progress",
        "campaign_summary",
    )

    ordering = (
        "event__event_date",
        "event__start_time",
    )

    inlines = [EventAdvertisementInline]

    fieldsets = (
        (
            "Campaign",
            {
                "fields": (
                    "event",
                    "status",
                    "campaign_progress",
                )
            },
        ),
        (
            "Advertising Summary",
            {
                "fields": (
                    "campaign_summary",
                )
            },
        ),
        (
            "Advertising Playbook",
            {
                "fields": (
                    "playbook",
                )
            },
        ),
        (
            "Generated Advertising Copy",
            {
                "fields": (
                    "advertising_title",
                    "short_description",
                    "long_description",
                    "facebook_copy",
                    "newsletter_copy",
                    "community_calendar_copy",
                    "email_copy",
                    "image_guidance",
                    "copy_generated_at",
                )
            },
        ),
        (
            "Generation Information",
            {
                "fields": (
                    "generated_at",
                    "generated_by",
                    "last_regenerated_at",
                )
            },
        ),
        (
            "Notes",
            {
                "fields": ("notes",)
            },
        ),
    )

    def get_urls(self):
        custom_urls = [
            path(
                "<path:object_id>/generate-advertising-copy/",
                self.admin_site.admin_view(
                    self.generate_advertising_copy_view
                ),
                name="outreach_advertisingcampaign_generate_copy",
            ),
        ]

        return custom_urls + super().get_urls()

    def generate_advertising_copy_view(
        self,
        request: HttpRequest,
        object_id: str,
    ) -> HttpResponse:
        campaign = self.get_object(request, object_id)

        if campaign is None:
            self.message_user(
                request,
                "The advertising campaign could not be found.",
                level=messages.ERROR,
            )

            return redirect(
                reverse(
                    "admin:outreach_advertisingcampaign_changelist"
                )
            )

        change_url = reverse(
            "admin:outreach_advertisingcampaign_change",
            args=[campaign.pk],
        )

        if not self.has_change_permission(request, campaign):
            self.message_user(
                request,
                "You do not have permission to modify this campaign.",
                level=messages.ERROR,
            )
            return redirect(change_url)

        if request.method != "POST":
            return redirect(change_url)

        if campaign.playbook is None:
            self.message_user(
                request,
                (
                    "Select and save an advertising playbook before "
                    "generating copy."
                ),
                level=messages.WARNING,
            )
            return redirect(change_url)

        try:
            generate_campaign_copy(
                campaign,
                overwrite_existing=False,
            )

        except ValueError as exc:
            self.message_user(
                request,
                str(exc),
                level=messages.WARNING,
            )

        except Exception as exc:
            self.message_user(
                request,
                f"Advertising copy could not be generated: {exc}",
                level=messages.ERROR,
            )

        else:
            self.message_user(
                request,
                (
                    "Advertising copy was generated using the "
                    f'"{campaign.playbook}" playbook. '
                    "Existing copy was preserved."
                ),
                level=messages.SUCCESS,
            )

        return redirect(change_url)

    @admin.display(description="Progress")
    def campaign_progress(self, obj):
        if not obj or not obj.pk:
            return "Campaign has not been saved."

        return (
            f"{obj.completed_outlets}/{obj.total_outlets} complete "
            f"({obj.progress_percent}%)"
        )

    @admin.display(description="Time Remaining")
    def estimated_time_remaining(self, obj):
        if not obj or not obj.pk:
            return "—"

        return self._format_minutes(
            obj.estimated_remaining_minutes
        )

    @admin.display(description="Campaign Summary")
    def campaign_summary(self, obj):
        if not obj or not obj.pk:
            return "Campaign has not been generated."

        event = obj.event

        if getattr(event, "advertise_to_full_service_area", False):
            coverage = "Full Service Area"
        else:
            radius = getattr(event, "advertising_radius_miles", None)
            coverage = (
                f"{radius:g} mile radius"
                if radius is not None
                else "No radius configured"
            )

        return format_html(
            """
            <div style="
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
                gap: 12px;
                max-width: 900px;
                margin-top: 8px;
            ">
                {}
                {}
                {}
                {}
                {}
                {}
                {}
                {}
            </div>
            """,
            self._summary_card(
                "Total Outlets",
                obj.total_outlets,
            ),
            self._summary_card(
                "Not Started",
                obj.not_started_count,
            ),
            self._summary_card(
                "Ready",
                obj.ready_count,
            ),
            self._summary_card(
                "Submitted",
                obj.submitted_count,
            ),
            self._summary_card(
                "Published",
                obj.published_count,
            ),
            self._summary_card(
                "Remaining",
                obj.remaining_count,
            ),
            self._summary_card(
                "Estimated Time",
                self._format_minutes(
                    obj.estimated_remaining_minutes
                ),
            ),
            self._summary_card(
                "Coverage",
                coverage,
            ),
        )

    @staticmethod
    def _summary_card(label, value):
        return format_html(
            """
            <div style="
                border: 1px solid var(--border-color, #d9d9d9);
                border-radius: 6px;
                padding: 14px;
                background: var(--body-bg, #ffffff);
                min-height: 72px;
            ">
                <div style="
                    color: var(--body-quiet-color, #666666);
                    font-size: 11px;
                    font-weight: 600;
                    margin-bottom: 6px;
                    text-transform: uppercase;
                    letter-spacing: 0.04em;
                ">
                    {}
                </div>

                <div style="
                    font-size: 20px;
                    font-weight: 600;
                    line-height: 1.2;
                ">
                    {}
                </div>
            </div>
            """,
            label,
            value,
        )

    @staticmethod
    def _format_minutes(minutes):
        minutes = int(minutes or 0)

        if minutes < 60:
            return f"{minutes} min"

        hours, remaining_minutes = divmod(minutes, 60)

        if remaining_minutes == 0:
            return "1 hour" if hours == 1 else f"{hours} hours"

        return f"{hours} hr {remaining_minutes} min"

@admin.register(EventAdvertisement)
class EventAdvertisementAdmin(admin.ModelAdmin):
    list_display = (
        "outlet",
        "campaign_event",
        "event_date",
        "submission_deadline",
        "status",
        "copy_status",
        "description_length",
        "submitted_by",
        "submitted_at",
    )

    list_filter = (
        "status",
        "submission_deadline",
        "copy_generated_at",
        "copy_reviewed_at",
        "submitted_at",
        "published_at",
        "outlet__category",
        "outlet__submission_method",
        "outlet__priority",
    )

    search_fields = (
        "campaign__event__event_name",
        "campaign__event__partner__partner_name",
        "campaign__event__partner__location_name",
        "outlet__name",
        "generated_title",
        "generated_description",
        "submitted_title",
        "submitted_description",
        "external_reference",
        "published_url",
        "notes",
    )

    autocomplete_fields = (
        "campaign",
        "outlet",
        "submitted_by",
    )

    readonly_fields = (
        "copy_generated_at",
        "copy_reviewed_at",
        "copy_reviewed_by",
        "generated_title_character_count",
        "generated_description_character_count",
        "submitted_title_character_count",
        "submitted_description_character_count",
        "created_at",
        "updated_at",
    )

    ordering = (
        "submission_deadline",
        "outlet__priority",
        "outlet__name",
    )

    date_hierarchy = "submission_deadline"

    actions = (
        "mark_copy_reviewed",
        "prepare_submission_copy",
    )

    fieldsets = (
        (
            "Advertisement",
            {
                "fields": (
                    "campaign",
                    "outlet",
                    "status",
                    "submission_deadline",
                )
            },
        ),
        (
            "Generated Copy",
            {
                "fields": (
                    "generated_title",
                    "generated_title_character_count",
                    "generated_description",
                    "generated_description_character_count",
                    "generated_email_subject",
                    "generated_email_body",
                    "copy_generated_at",
                )
            },
        ),
        (
            "Copy Review",
            {
                "fields": (
                    "copy_reviewed_at",
                    "copy_reviewed_by",
                )
            },
        ),
        (
            "Final Submission Copy",
            {
                "fields": (
                    "submitted_title",
                    "submitted_title_character_count",
                    "submitted_description",
                    "submitted_description_character_count",
                    "submitted_email_subject",
                    "submitted_email_body",
                )
            },
        ),
        (
            "Submission Tracking",
            {
                "fields": (
                    "submitted_at",
                    "submitted_by",
                    "external_reference",
                )
            },
        ),
        (
            "Publication Tracking",
            {
                "fields": (
                    "published_at",
                    "published_url",
                )
            },
        ),
        (
            "Notes",
            {
                "fields": (
                    "notes",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": (
                    "collapse",
                ),
            },
        ),
    )

    def campaign_event(self, obj):
        return obj.campaign.event.event_name

    campaign_event.short_description = "Event"
    campaign_event.admin_order_field = "campaign__event__event_name"

    def event_date(self, obj):
        return obj.campaign.event.event_date

    event_date.short_description = "Event Date"
    event_date.admin_order_field = "campaign__event__event_date"

    def copy_status(self, obj):
        if obj.copy_reviewed_at:
            return "Reviewed"

        if obj.copy_generated_at:
            return "Generated"

        return "Not Generated"

    copy_status.short_description = "Copy"

    def description_length(self, obj):
        current_length = len(obj.generated_description or "")
        maximum_length = obj.outlet.maximum_description_characters

        if maximum_length:
            return f"{current_length} / {maximum_length}"

        return str(current_length)

    description_length.short_description = "Description Length"

    def generated_title_character_count(self, obj):
        current_length = len(obj.generated_title or "")
        maximum_length = obj.outlet.maximum_title_characters

        if maximum_length:
            return f"{current_length} / {maximum_length}"

        return f"{current_length} characters"

    generated_title_character_count.short_description = (
        "Generated Title Characters"
    )

    def generated_description_character_count(self, obj):
        current_length = len(obj.generated_description or "")
        maximum_length = obj.outlet.maximum_description_characters

        if maximum_length:
            return f"{current_length} / {maximum_length}"

        return f"{current_length} characters"

    generated_description_character_count.short_description = (
        "Generated Description Characters"
    )

    def submitted_title_character_count(self, obj):
        current_length = len(obj.submitted_title or "")
        maximum_length = obj.outlet.maximum_title_characters

        if maximum_length:
            return f"{current_length} / {maximum_length}"

        return f"{current_length} characters"

    submitted_title_character_count.short_description = (
        "Submitted Title Characters"
    )

    def submitted_description_character_count(self, obj):
        current_length = len(obj.submitted_description or "")
        maximum_length = obj.outlet.maximum_description_characters

        if maximum_length:
            return f"{current_length} / {maximum_length}"

        return f"{current_length} characters"

    submitted_description_character_count.short_description = (
        "Submitted Description Characters"
    )

    @admin.action(description="Mark selected copy as reviewed")
    def mark_copy_reviewed(self, request, queryset):
        reviewed_count = 0
        skipped_count = 0

        for advertisement in queryset:
            if not (
                advertisement.generated_title
                or advertisement.generated_description
                or advertisement.generated_email_subject
                or advertisement.generated_email_body
            ):
                skipped_count += 1
                continue

            advertisement.copy_reviewed_at = timezone.now()
            advertisement.copy_reviewed_by = request.user
            advertisement.status = EventAdvertisement.Status.READY

            advertisement.save(
                update_fields=[
                    "copy_reviewed_at",
                    "copy_reviewed_by",
                    "status",
                    "updated_at",
                ]
            )

            reviewed_count += 1

        if reviewed_count:
            self.message_user(
                request,
                f"{reviewed_count} advertisement(s) marked as reviewed.",
                level=messages.SUCCESS,
            )

        if skipped_count:
            self.message_user(
                request,
                (
                    f"{skipped_count} advertisement(s) were skipped because "
                    "they did not contain generated copy."
                ),
                level=messages.WARNING,
            )

    @admin.action(description="Prepare final submission copy")
    def prepare_submission_copy(self, request, queryset):
        prepared_count = 0
        skipped_count = 0

        for advertisement in queryset:
            if not advertisement.copy_reviewed_at:
                skipped_count += 1
                continue

            advertisement.submitted_title = advertisement.generated_title
            advertisement.submitted_description = (
                advertisement.generated_description
            )
            advertisement.submitted_email_subject = (
                advertisement.generated_email_subject
            )
            advertisement.submitted_email_body = (
                advertisement.generated_email_body
            )

            advertisement.save(
                update_fields=[
                    "submitted_title",
                    "submitted_description",
                    "submitted_email_subject",
                    "submitted_email_body",
                    "updated_at",
                ]
            )

            prepared_count += 1

        if prepared_count:
            self.message_user(
                request,
                (
                    f"Final submission copy prepared for "
                    f"{prepared_count} advertisement(s)."
                ),
                level=messages.SUCCESS,
            )

        if skipped_count:
            self.message_user(
                request,
                (
                    f"{skipped_count} advertisement(s) were skipped because "
                    "their copy has not been reviewed."
                ),
                level=messages.WARNING,
            )

@admin.register(AdvertisingPlaybook)
class AdvertisingPlaybookAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "voice",
        "target_audience",
        "active",
        "updated_at",
    )

    list_filter = (
        "active",
        "voice",
        "target_audience",
    )

    search_fields = (
        "name",
        "description",
        "key_messages",
        "avoid_language",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "General",
            {
                "fields": (
                    "name",
                    "description",
                    "active",
                ),
            },
        ),
        (
            "Advertising Strategy",
            {
                "fields": (
                    "voice",
                    "target_audience",
                    "key_messages",
                    "avoid_language",
                ),
            },
        ),
        (
            "Advertising Templates",
            {
                "fields": (
                    "short_description_template",
                    "long_description_template",
                    "facebook_template",
                    "newsletter_template",
                    "community_calendar_template",
                    "email_template",
                ),
            },
        ),
        (
            "Generated Copy Types",
            {
                "fields": (
                    "generate_facebook_copy",
                    "generate_newsletter_copy",
                    "generate_calendar_copy",
                    "generate_email_copy",
                ),
            },
        ),
        (
            "Images and Automation",
            {
                "fields": (
                    "image_guidance",
                    "automation_notes",
                ),
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": (
                    "collapse",
                ),
            },
        ),
    )