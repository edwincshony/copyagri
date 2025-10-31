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

# farmer/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.db import transaction
from farmer.models import ProductListing, Bid
from buyer.models import Purchase

@receiver(post_save, sender=Bid)
def close_if_expired(sender, instance, **kwargs):
    listing = instance.listing

    # Stop if already inactive or has no bid end time
    if not listing.is_active or not listing.bid_end_time:
        return

    # Stop if the bid time hasn’t expired yet
    if listing.bid_end_time >= timezone.now():
        return

    # Prevent recursive signal triggering
    if getattr(listing, "_closing", False):
        return

    listing._closing = True

    try:
        with transaction.atomic():
            listing.refresh_from_db()

            if not listing.is_active:
                return  # Already closed elsewhere

            highest_bid = listing.highest_bid()
            if highest_bid:
                # Mark bid as accepted
                highest_bid.is_accepted = True
                highest_bid.save(update_fields=["is_accepted"])

                # ✅ Create purchase if not exists, or update if needed
                purchase, created = Purchase.objects.get_or_create(
                    buyer=highest_bid.bidder,
                    listing=listing,
                    defaults={
                        "quantity": listing.quantity,
                        "total_price": highest_bid.amount,
                    },
                )
                if not created:
                    purchase.quantity = listing.quantity
                    purchase.total_price = highest_bid.amount
                    purchase.save(update_fields=["quantity", "total_price"])

            # Close the listing safely
            listing.is_active = False
            listing.save(update_fields=["is_active"])

    finally:
        # Always clean up the temporary flag
        if hasattr(listing, "_closing"):
            del listing._closing



