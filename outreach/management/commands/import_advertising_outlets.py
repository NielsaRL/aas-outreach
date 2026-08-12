import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from outreach.models import AdvertisingOutlet


TRUE_VALUES = {
    "1",
    "true",
    "yes",
    "y",
    "on",
    "checked",
}

FALSE_VALUES = {
    "0",
    "false",
    "no",
    "n",
    "off",
    "unchecked",
    "",
}


def clean_text(value):
    if value is None:
        return ""

    return str(value).strip()


def parse_boolean(value, field_name, row_number):
    cleaned_value = clean_text(value).lower()

    if cleaned_value in TRUE_VALUES:
        return True

    if cleaned_value in FALSE_VALUES:
        return False

    raise CommandError(
        f"Row {row_number}: invalid boolean value "
        f"'{value}' for '{field_name}'."
    )


def parse_optional_integer(value, field_name, row_number):
    cleaned_value = clean_text(value)

    if not cleaned_value:
        return None

    try:
        parsed_value = int(cleaned_value)
    except ValueError as exc:
        raise CommandError(
            f"Row {row_number}: '{value}' is not a valid integer "
            f"for '{field_name}'."
        ) from exc

    if parsed_value < 0:
        raise CommandError(
            f"Row {row_number}: '{field_name}' cannot be negative."
        )

    return parsed_value


def parse_required_integer(
    value,
    field_name,
    row_number,
    default=None,
):
    cleaned_value = clean_text(value)

    if not cleaned_value:
        if default is not None:
            return default

        raise CommandError(
            f"Row {row_number}: '{field_name}' is required."
        )

    return parse_optional_integer(
        cleaned_value,
        field_name,
        row_number,
    )


def normalize_choice(
    value,
    valid_choices,
    field_name,
    row_number,
    default=None,
):
    cleaned_value = clean_text(value)

    if not cleaned_value:
        if default is not None:
            return default

        raise CommandError(
            f"Row {row_number}: '{field_name}' is required."
        )

    normalized_value = (
        cleaned_value
        .upper()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
    )

    valid_values = {
        choice_value
        for choice_value, _choice_label in valid_choices
    }

    label_lookup = {
        (
            choice_label
            .upper()
            .replace(" ", "_")
            .replace("-", "_")
            .replace("/", "_")
        ): choice_value
        for choice_value, choice_label in valid_choices
    }

    if normalized_value in valid_values:
        return normalized_value

    if normalized_value in label_lookup:
        return label_lookup[normalized_value]

    valid_display_values = ", ".join(sorted(valid_values))

    raise CommandError(
        f"Row {row_number}: invalid value '{value}' for "
        f"'{field_name}'. Valid values are: "
        f"{valid_display_values}."
    )


class Command(BaseCommand):
    help = (
        "Import or update AdvertisingOutlet records from a CSV file. "
        "Existing outlets are matched case-insensitively by name."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_file",
            type=str,
            help="Path to the advertising-outlet CSV file.",
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help=(
                "Validate and preview the import without saving changes."
            ),
        )

        parser.add_argument(
            "--skip-errors",
            action="store_true",
            help=(
                "Skip invalid rows and continue importing the remaining "
                "rows."
            ),
        )

    @transaction.atomic
    def handle(self, *args, **options):
        csv_path = Path(options["csv_file"]).expanduser().resolve()
        dry_run = options["dry_run"]
        skip_errors = options["skip_errors"]

        if not csv_path.exists():
            raise CommandError(
                f"CSV file does not exist: {csv_path}"
            )

        if not csv_path.is_file():
            raise CommandError(
                f"CSV path is not a file: {csv_path}"
            )

        created_count = 0
        updated_count = 0
        unchanged_count = 0
        skipped_count = 0

        try:
            csv_handle = csv_path.open(
                mode="r",
                encoding="utf-8-sig",
                newline="",
            )
        except OSError as exc:
            raise CommandError(
                f"Could not open CSV file: {exc}"
            ) from exc

        with csv_handle:
            reader = csv.DictReader(csv_handle)

            if not reader.fieldnames:
                raise CommandError(
                    "The CSV file does not contain a header row."
                )

            normalized_headers = {
                clean_text(header).lower()
                for header in reader.fieldnames
                if header
            }

            if "name" not in normalized_headers:
                raise CommandError(
                    "The CSV must contain a 'name' column."
                )

            for row_number, raw_row in enumerate(reader, start=2):
                row = {
                    clean_text(key).lower(): value
                    for key, value in raw_row.items()
                    if key is not None
                }

                try:
                    result = self.import_row(
                        row=row,
                        row_number=row_number,
                    )
                except CommandError as exc:
                    if not skip_errors:
                        raise

                    skipped_count += 1
                    self.stderr.write(
                        self.style.WARNING(str(exc))
                    )
                    continue

                if result == "created":
                    created_count += 1
                elif result == "updated":
                    updated_count += 1
                else:
                    unchanged_count += 1

        if dry_run:
            transaction.set_rollback(True)

            self.stdout.write(
                self.style.WARNING(
                    "Dry run complete. No database changes were saved."
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                (
                    f"Import complete: {created_count} created, "
                    f"{updated_count} updated, "
                    f"{unchanged_count} unchanged, "
                    f"{skipped_count} skipped."
                )
            )
        )

    def import_row(self, row, row_number):
        name = clean_text(row.get("name"))

        if not name:
            raise CommandError(
                f"Row {row_number}: 'name' is required."
            )

        category = normalize_choice(
            value=row.get("category"),
            valid_choices=AdvertisingOutlet.Category.choices,
            field_name="category",
            row_number=row_number,
            default=AdvertisingOutlet.Category.COMMUNITY_CALENDAR,
        )

        submission_method = normalize_choice(
            value=row.get("submission_method"),
            valid_choices=AdvertisingOutlet.SubmissionMethod.choices,
            field_name="submission_method",
            row_number=row_number,
            default=AdvertisingOutlet.SubmissionMethod.MANUAL_FORM,
        )

        priority = parse_required_integer(
            value=row.get("priority"),
            field_name="priority",
            row_number=row_number,
            default=AdvertisingOutlet.Priority.NORMAL,
        )

        valid_priorities = {
            choice_value
            for choice_value, _choice_label
            in AdvertisingOutlet.Priority.choices
        }

        if priority not in valid_priorities:
            raise CommandError(
                f"Row {row_number}: invalid priority '{priority}'. "
                f"Valid priorities are "
                f"{sorted(valid_priorities)}."
            )

        defaults = {
            "category": category,
            "submission_method": submission_method,
            "priority": priority,
            "website_url": clean_text(
                row.get("website_url")
            ),
            "submission_url": clean_text(
                row.get("submission_url")
            ),
            "contact_name": clean_text(
                row.get("contact_name")
            ),
            "contact_email": clean_text(
                row.get("contact_email")
            ),
            "contact_phone": clean_text(
                row.get("contact_phone")
            ),
            "city": clean_text(row.get("city")),
            "county": clean_text(row.get("county")),
            "state": clean_text(row.get("state")) or "Texas",
            "service_radius_miles": parse_optional_integer(
                row.get("service_radius_miles"),
                "service_radius_miles",
                row_number,
            ),
            "minimum_lead_days": parse_required_integer(
                row.get("minimum_lead_days"),
                "minimum_lead_days",
                row_number,
                default=0,
            ),
            "preferred_lead_days": parse_optional_integer(
                row.get("preferred_lead_days"),
                "preferred_lead_days",
                row_number,
            ),
            "accepts_star_parties": parse_boolean(
                row.get("accepts_star_parties", "true"),
                "accepts_star_parties",
                row_number,
            ),
            "accepts_solar_outreach": parse_boolean(
                row.get("accepts_solar_outreach", "true"),
                "accepts_solar_outreach",
                row_number,
            ),
            "accepts_library_programs": parse_boolean(
                row.get("accepts_library_programs", "true"),
                "accepts_library_programs",
                row_number,
            ),
            "accepts_sidewalk_astronomy": parse_boolean(
                row.get(
                    "accepts_sidewalk_astronomy",
                    "true",
                ),
                "accepts_sidewalk_astronomy",
                row_number,
            ),
            "accepts_custom_events": parse_boolean(
                row.get("accepts_custom_events", "true"),
                "accepts_custom_events",
                row_number,
            ),
            "requires_account": parse_boolean(
                row.get("requires_account", "false"),
                "requires_account",
                row_number,
            ),
            "requires_image": parse_boolean(
                row.get("requires_image", "false"),
                "requires_image",
                row_number,
            ),
            "requires_approval": parse_boolean(
                row.get("requires_approval", "false"),
                "requires_approval",
                row_number,
            ),
            "active": parse_boolean(
                row.get("active", "true"),
                "active",
                row_number,
            ),
            "submission_instructions": clean_text(
                row.get("submission_instructions")
            ),
            "notes": clean_text(row.get("notes")),
            "covers_full_service_area": parse_boolean(
                row.get("covers_full_service_area", "false"),
                "covers_full_service_area",
                row_number,
            ),
            "estimated_submission_minutes": parse_required_integer(
                row.get("estimated_submission_minutes"),
                "estimated_submission_minutes",
                row_number,
                default=5,
            ),
        }

        existing_outlet = (
            AdvertisingOutlet.objects
            .filter(name__iexact=name)
            .first()
        )

        if existing_outlet is None:
            AdvertisingOutlet.objects.create(
                name=name,
                **defaults,
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Row {row_number}: created '{name}'."
                )
            )

            return "created"

        changed_fields = []

        if existing_outlet.name != name:
            existing_outlet.name = name
            changed_fields.append("name")

        for field_name, new_value in defaults.items():
            old_value = getattr(existing_outlet, field_name)

            if old_value != new_value:
                setattr(existing_outlet, field_name, new_value)
                changed_fields.append(field_name)

        if not changed_fields:
            self.stdout.write(
                f"Row {row_number}: unchanged '{name}'."
            )
            return "unchanged"

        existing_outlet.save(
            update_fields=changed_fields + ["updated_at"]
        )

        self.stdout.write(
            self.style.WARNING(
                f"Row {row_number}: updated '{name}'."
            )
        )

        return "updated"