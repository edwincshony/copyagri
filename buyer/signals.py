from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Purchase
from farmer.models import Bid

@receiver(post_save, sender=Purchase)
def purchase_notification(sender, instance, created, **kwargs):
    if created:
        send_mail(
            'Purchase Confirmed',
            f'Your purchase of {instance.quantity} units of {instance.listing.name} has been confirmed.',
            settings.DEFAULT_FROM_EMAIL,
            [instance.buyer.email],
            fail_silently=True,
        )
        # Notify farmer
        send_mail(
            'New Purchase Order',
            f'{instance.buyer.username} purchased {instance.quantity} units of your {instance.listing.name}.',
            settings.DEFAULT_FROM_EMAIL,
            [instance.listing.user.email],
            fail_silently=True,
        )

@receiver(post_save, sender=Bid)
def bid_notification(sender, instance, created, **kwargs):
    if created:
        send_mail(
            'New Bid Placed',
            f'Your bid of ₹{instance.amount} on {instance.listing.name} has been placed.',
            settings.DEFAULT_FROM_EMAIL,
            [instance.bidder.email],
            fail_silently=True,
        )
        # Notify farmer
        send_mail(
            'New Bid on Your Listing',
            f'{instance.bidder.username} placed a bid of ₹{instance.amount} on {instance.listing.name}.',
            settings.DEFAULT_FROM_EMAIL,
            [instance.listing.user.email],
            fail_silently=True,
        )