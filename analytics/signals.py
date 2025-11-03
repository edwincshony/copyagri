from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from accounts.models import CustomUser
from farmer.models import ProductListing
from farmer.models import CultivationBooking, StorageBooking
from .models import AnalyticsData
from .views import generate_analytics_data

@receiver([post_save, post_delete], sender=CustomUser)
@receiver([post_save, post_delete], sender=ProductListing)
@receiver([post_save, post_delete], sender=CultivationBooking)
@receiver([post_save, post_delete], sender=StorageBooking)
def update_analytics(sender, **kwargs):
    """
    Update analytics data whenever there's a change in users, listings, or bookings
    """
    today = timezone.now().date()
    generate_analytics_data()