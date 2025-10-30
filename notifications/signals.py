from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Notification
from accounts.models import CustomUser
from adminpanel.models import UserDocument
from farmer.models import CultivationBooking, StorageBooking, Bid, ProductListing

@receiver(post_save, sender=CustomUser)
def user_approval_notification(sender, instance, **kwargs):
    if instance.is_approved != instance._state.adding:  # Changed
        status = 'Approved' if instance.is_approved else 'Rejected'
        Notification.objects.create(
            user=instance,
            title=f'Account {status}',
            message=f'Your AgriLeader account has been {status.lower()}.',
            notification_type='approval'
        )
        # Email as before

@receiver(post_save, sender=UserDocument)
def document_notification(sender, instance, created, **kwargs):
    if not created and instance.status != 'pending':
        status = instance.status
        Notification.objects.create(
            user=instance.user,
            title=f'Document {status.title()}',
            message=f'Your {instance.document_type} has been {status}.',
            notification_type='approval',
            related_id=instance.id,
            related_model='UserDocument'
        )

@receiver(post_save, sender=CultivationBooking)
@receiver(post_save, sender=StorageBooking)
def booking_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.user,
            title='Booking Request Submitted',
            message=f'Your booking for {instance.slot.name} is pending approval.',
            notification_type='booking',
            related_id=instance.id,
            related_model=sender.__name__
        )
    elif instance.status != 'pending':
        Notification.objects.create(
            user=instance.user,
            title=f'Booking {instance.status.title()}',
            message=f'Your booking for {instance.slot.name} has been {instance.status}.',
            notification_type='booking',
            related_id=instance.id,
            related_model=sender.__name__
        )

@receiver(post_save, sender=Bid)
def bid_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            bidder=instance.bidder,
            title='Bid Placed',
            message=f'Your bid of ₹{instance.amount} on {instance.listing.name} has been placed.',
            notification_type='marketplace'
        )
        Notification.objects.create(
            user=instance.listing.user,
            title='New Bid Received',
            message=f'{instance.bidder.username} bid ₹{instance.amount} on your {instance.listing.name}.',
            notification_type='marketplace',
            related_id=instance.id,
            related_model='Bid'
        )
    elif instance.is_accepted:
        Notification.objects.create(
            bidder=instance.bidder,
            title='Bid Accepted',
            message=f'Your bid on {instance.listing.name} has been accepted.',
            notification_type='marketplace'
        )

@receiver(post_save, sender=ProductListing)
def listing_approval_notification(sender, instance, created, **kwargs):
    if created:
        # Placeholder: Admin approval for listings (add status if needed)
        pass