from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Report
from farmer.models import CultivationBooking, StorageBooking
from buyer.models import Purchase
from accounts.models import CustomUser

@receiver(post_save, sender=CultivationBooking)
@receiver(post_save, sender=StorageBooking)
@receiver(post_save, sender=Purchase)
@receiver(post_save, sender=CustomUser)
def refresh_active_reports(sender, instance, **kwargs):
    from datetime import date
    reports = Report.objects.filter(end_date__gte=date.today(), is_auto_generated=True)
    for r in reports:
        r.update_data()


# Weather auto-generation (simulated; real: API signal)
@receiver(post_save, sender=CustomUser)
def auto_generate_weather_alert(sender, instance, created, **kwargs):
    if created and instance.role in ['farmer', 'buyer']:
        from analytics.models import WeatherAlert
        WeatherAlert.objects.create(
            user=instance,
            location=instance.address,
            alert_type='Welcome Weather Check',
            description='Check local forecasts for optimal sowing.',
            severity='low'
        )