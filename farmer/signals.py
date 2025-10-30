from django.dispatch import receiver
from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.core.mail import send_mail
from .models import CultivationBooking, StorageBooking


@receiver(pre_save, sender=CultivationBooking)
def handle_cultivation_approval(sender, instance, **kwargs):
    """Reduce available area only when booking gets approved for the first time."""
    if not instance.pk:
        return  # Skip new bookings (created, not yet saved)
    
    previous = CultivationBooking.objects.get(pk=instance.pk)
    
    # Detect status change from pending/rejected -> approved
    if previous.status != 'approved' and instance.status == 'approved':
        if instance.booked_area_acres > instance.slot.available_area_acres:
            raise ValueError("Cannot approve — not enough available area.")
        instance.slot.available_area_acres -= instance.booked_area_acres
        instance.slot.save()


@receiver(pre_save, sender=StorageBooking)
def handle_storage_approval(sender, instance, **kwargs):
    """Reduce available slots only when booking gets approved for the first time."""
    if not instance.pk:
        return
    
    previous = StorageBooking.objects.get(pk=instance.pk)
    
    if previous.status != 'approved' and instance.status == 'approved':
        if instance.booked_slots > instance.slot.available_slots:
            raise ValueError("Cannot approve — not enough available slots.")
        instance.slot.available_slots -= instance.booked_slots
        instance.slot.save()


@receiver(post_save, sender=CultivationBooking)
@receiver(post_save, sender=StorageBooking)
def send_booking_notification(sender, instance, created, **kwargs):
    """Notify user of new booking submission."""
    if created:
        send_mail(
            'Booking Request Received',
            f'Your booking for {instance.slot.name} is pending admin approval.',
            settings.DEFAULT_FROM_EMAIL,
            [instance.user.email],
            fail_silently=True,
        )
