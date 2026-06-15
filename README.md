# AAS Outreach Scheduler

A Django-based application for planning, scheduling, and managing astronomy outreach events for the Austin Astronomical Society (AAS).

The system combines event scheduling, astronomical calculations, volunteer management, weather forecasting, and event preparation tools into a single application.

---

## Features

### Event Scheduling

- Partner-based scheduling
- Configurable event priorities
- Moon preference support
- Even distribution of events throughout the year
- Manual approval workflow
- Suggested event generation

### Event Information

Automatic calculation of:

- Sunset time
- Civil dusk
- Nautical dusk
- Moon phase
- Moon illumination
- Suggested talk start time
- Suggested laser tour time

### Astronomy

- Curated astronomical targets
- Dynamic planetary targets using Skyfield
- Visibility filtering
- Minimum altitude requirements
- Event-specific target lists
- Talking point support

### Weather Integration

National Weather Service (NWS) forecast support including:

- Heat index
- Temperature
- Wind speed
- Rain probability
- Thunder probability
- Cloud cover
- Watches and warnings
- Forecast summaries

### Volunteer Management

- Volunteer roster
- Host assignments
- Event volunteers
- Event logs

### Event Checklists

Per-event task management with:

- TODO status
- DONE status
- NA status
- Progress tracking
- Event-specific checklist items
- Cancellation workflows
- Special partner procedures

### Calendar View

- Monthly calendar display
- Event navigation
- Month-to-month browsing
- Visual overview of outreach activities

---

## Technology Stack

- Python 3.13
- Django 6
- SQLite (development)
- Skyfield
- Astral
- NOAA / National Weather Service API

---

## Installation

Clone the repository:

```bash
git clone https://github.com/NielsaRL/aas-outreach.git
cd aas-outreach
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the environment:

### Windows

```bash
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run database migrations:

```bash
python manage.py migrate
```

Create an administrator account:

```bash
python manage.py createsuperuser
```

Start the development server:

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/admin/
```

---

## Main Models

### Partner

Stores outreach locations and scheduling preferences.

Examples:

- Public Star Parties
- Libraries
- Schools
- Parks

### SuggestedEvent

Generated events awaiting approval.

### ScheduledEvent

Approved outreach events containing:

- Dates
- Times
- Hosts
- Weather information
- Moon information
- Attendance estimates

### Volunteer

Volunteer roster information.

### EventVolunteer

Volunteer assignments for specific events.

### EventLog

Stores post-event notes and outcomes.

### AstronomicalTarget

Catalog of astronomical objects and educational targets.

### EventTarget

Objects associated with a specific event.

### EventChecklistItem

Task tracking for individual outreach events.

### SchedulerRun

Tracks automatic scheduling runs.

---

## Services

```text
outreach/services/

scheduler.py
targets.py
weather.py
star_chart.py
```

### scheduler.py

Generates suggested events based on:

- Partner priorities
- Allowed months
- Allowed weekdays
- Moon preferences

### targets.py

Suggests observable objects and talking points.

### weather.py

Retrieves forecast information from the National Weather Service.

### star_chart.py

Generates printable event star charts.

---

## Admin Features

### Scheduled Events

- Volunteer assignments
- Target assignments
- Event logs
- Weather updates
- Sky chart links

### Event Checklists

- Progress tracking
- TODO / DONE / NA status
- Event preparation workflows

### Suggested Events

Bulk actions:

- Approve suggestions
- Reject suggestions

---

## Astronomy Support

### Skyfield

Used for:

- Planet positions
- Moon calculations

### Astral

Used for:

- Sunset calculations
- Civil dusk
- Nautical dusk

---

## Future Enhancements

Planned features include:

- Star chart PDF generation
- Email automation
- Outreach committee support
- Statistics dashboard
- Attendance reporting
- Equipment tracking
- Partner capability flags
- FullCalendar.js integration

---

## Repository

GitHub:

```text
https://github.com/NielsaRL/aas-outreach
```

---

## License

This project is intended for use by the Austin Astronomical Society and contributors.

---

Clear skies! 🌙🔭
