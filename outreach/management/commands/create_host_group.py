from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create Host Access group with view/add/change permissions but no delete permissions."

    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(name="Host Access")

        permissions = Permission.objects.filter(
            content_type__app_label="outreach"
        ).exclude(
            codename__startswith="delete_"
        )

        group.permissions.set(permissions)

        self.stdout.write(
            self.style.SUCCESS(
                f"Host Access group updated with {permissions.count()} permissions."
            )
        )