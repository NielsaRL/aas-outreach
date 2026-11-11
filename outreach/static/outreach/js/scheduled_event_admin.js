
document.addEventListener("DOMContentLoaded", function () {
    const eventType = document.getElementById("id_event_title_type");

    if (!eventType) {
        return;
    }

    const steamHiddenFields = [
        // Advertising
        "advertising_radius_miles",
        "advertise_to_full_service_area",
        "advertising_campaign_link",
        "advertising_progress",

        // Weather
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

        // Twilight and moon
        "sunset_time",
        "civil_dusk_time",
        "nautical_dusk_time",
        "moonrise_time",
        "moon_illumination",
        "moon_phase",

        // Sky chart and suggested observing times
        "night_sky_chart_link",
        "suggested_talk_start_time",
        "suggested_laser_tour_time"
    ];

    function updateEventForm() {
        const isSteam = eventType.value === "STEAM_EVENT";

        steamHiddenFields.forEach(function (fieldName) {
            const row = document.querySelector(
                ".field-" + fieldName
            );

            if (row) {
                row.style.display = isSteam ? "none" : "";
            }
        });

        // Hide Event Targets for STEAM events.
        const eventTargetsSection = document.getElementById(
            "event_targets-group"
        );

        if (eventTargetsSection) {
            eventTargetsSection.style.display = isSteam ? "none" : "";
        }
    }

    eventType.addEventListener("change", updateEventForm);

    updateEventForm();
});
