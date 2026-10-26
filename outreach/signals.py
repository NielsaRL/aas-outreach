
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .models import SchedulerRun, SuggestedEvent


@receiver(pre_delete, sender=SchedulerRun)
def cleanup_scheduler_run_suggestions(sender, instance, **kwargs):
    """
    Remove generated, unapproved suggestions when their scheduler
    run is deleted.

    Preserve approved and manually entered suggestions.
    """
    SuggestedEvent.objects.filter(
        scheduler_run=instance,
        manual_entry=False,
        status__in=["SUGGESTED", "REJECTED"],
    ).delete()
