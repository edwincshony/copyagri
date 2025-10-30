from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Report

@receiver(post_save, sender=Report)
def notify_report_generated(sender, instance, created, **kwargs):
    if created:
        # Placeholder: Send email to admin or users
        pass