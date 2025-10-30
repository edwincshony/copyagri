from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import CultivationBooking, StorageBooking

@receiver(post_save, sender=CultivationBooking)
def update_cult_availability(sender, instance, **kwargs):
    if instance.status == 'approved':
        instance.slot.available_area_acres -= instance.booked_area_acres
        instance.slot.save()

@receiver(post_save, sender=StorageBooking)
def update_storage_availability(sender, instance, **kwargs):
    if instance.status == 'approved':
        instance.slot.available_slots -= instance.booked_slots
        instance.slot.save()

@receiver(post_save, sender=CultivationBooking)
@receiver(post_save, sender=StorageBooking)
def send_booking_notification(sender, instance, created, **kwargs):
    if created:
        send_mail(
            'Booking Request Received',
            f'Your booking for {instance.slot.name} is pending approval.',
            settings.DEFAULT_FROM_EMAIL,
            [instance.user.email],
            fail_silently=True,
        )